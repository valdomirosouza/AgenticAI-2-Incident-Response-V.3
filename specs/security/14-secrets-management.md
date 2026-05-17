# Spec 14: Secrets Management

**Domain**: security
**Owner**: Security Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #12
**Linked ADRs**: ADR-0020
**Review cadence**: Every release or on secret rotation event

---

## 1. Purpose

Define the Vault policy, secret catalogue, rotation schedule per secret type, audit
rules and emergency revocation procedure for all secrets used by the Copilot.

---

## 2. Context

ADR-0020 adopted HashiCorp Vault OSS with AppRole authentication and Vault Agent sidecar
as the zero-trust secrets management solution. No secrets may be stored in environment
variables, `.env` files, Kubernetes Secrets (base64 only) or the repository. This spec
operationalises that decision: what secrets exist, where they live, how long they live,
and how they are revoked.

---

## 3. Decision

### 3.1 Secret catalogue

| Secret ID | Secret                          | Vault path                             | Consumer             | Auth method           |
| --------- | ------------------------------- | -------------------------------------- | -------------------- | --------------------- |
| S-01      | Anthropic API key               | `secret/data/llm/anthropic_key`        | `llm_adapter`        | AppRole + Vault Agent |
| S-02      | HITL signing key (HMAC-SHA256)  | `secret/data/hitl/signing_key`         | `action_executor`    | AppRole + Vault Agent |
| S-03      | Audit trail GCS service account | `secret/data/audit/gcs_sa_key`         | `audit_adapter`      | AppRole + Vault Agent |
| S-04      | Prometheus remote write token   | `secret/data/observability/prom_token` | OTel Collector       | AppRole + Vault Agent |
| S-05      | Loki push token                 | `secret/data/observability/loki_token` | OTel Collector       | AppRole + Vault Agent |
| S-06      | GitHub Actions OIDC token       | Federated via GitHub OIDC              | `.github/workflows/` | OIDC (no static key)  |
| S-07      | Vault AppRole `role_id`         | Non-secret; baked into pod spec        | All services         | —                     |
| S-08      | Vault AppRole `secret_id`       | Injected by Vault Agent at startup     | All services         | Kubernetes SA         |

S-06 uses GitHub's OIDC federation — no long-lived static token is stored anywhere.
S-07 (`role_id`) is not sensitive and may be in the pod spec. S-08 (`secret_id`) is
wrapped and injected by Vault Agent; it never appears in logs or pod env vars.

### 3.2 Vault policy per AppRole

Each service has a dedicated AppRole with the minimum required policy:

```hcl
# llm-adapter policy
path "secret/data/llm/anthropic_key" {
  capabilities = ["read"]
}

# action-executor policy
path "secret/data/hitl/signing_key" {
  capabilities = ["read"]
}

# audit-adapter policy
path "secret/data/audit/gcs_sa_key" {
  capabilities = ["read"]
}
```

No service has `create`, `update`, `delete` or `list` capabilities on secret paths.
The Vault admin role (Tech Lead only) is the sole writer. Policies are version-controlled
in `infrastructure/vault/policies/`.

### 3.3 Rotation schedule

| Secret ID | Rotation trigger                    | Rotation interval | Automated?                                     | Owner     |
| --------- | ----------------------------------- | ----------------- | ---------------------------------------------- | --------- |
| S-01      | Anthropic key compromise or 90 days | 90 days           | Manual (Anthropic portal)                      | Tech Lead |
| S-02      | HITL compromise event or 30 days    | 30 days           | Manual via Vault CLI                           | Tech Lead |
| S-03      | GCS SA key compromise or 90 days    | 90 days           | Manual (GCP IAM)                               | Tech Lead |
| S-04      | 30 days                             | 30 days           | Vault dynamic secrets (if Prometheus supports) | Automated |
| S-05      | 30 days                             | 30 days           | Vault dynamic secrets (if Loki supports)       | Automated |
| S-08      | Every pod restart                   | Pod lifecycle     | Vault Agent response-wrapping                  | Automated |

Vault Agent leases for S-08 have a TTL of 1 hour and are auto-renewed while the pod
is running. On pod termination, the lease is revoked.

### 3.4 Secret access audit rules

Every secret read from Vault generates an audit log entry in Vault's audit device
(file backend, forwarded to Loki):

```json
{
  "type": "response",
  "auth": { "accessor": "...", "policies": ["llm-adapter"] },
  "request": { "operation": "read", "path": "secret/data/llm/anthropic_key" },
  "response": { "data": "[REDACTED]" }
}
```

Vault audit logs are:

- Forwarded to the same Loki instance as application logs (separate stream `{job="vault"}`)
- Retained for 2 years (same as audit trail — ADR-0030)
- Monitored for anomalous access patterns: any read outside business hours or from an
  unexpected IP triggers a P2 alert

### 3.5 Emergency revocation procedure

Triggered by: suspected secret compromise, kill-switch activation (ADR-0025), or
security incident involving a Copilot service.

```
Step 1  Identify compromised secret(s) from audit log or incident report
Step 2  Revoke Vault AppRole secret_id immediately:
        vault write -force auth/approle/role/<role>/secret-id-accessor/destroy \
          secret_id_accessor=<accessor>
Step 3  Revoke any active leases for the affected path:
        vault lease revoke -prefix secret/data/llm/
Step 4  Rotate the underlying secret at source (Anthropic portal / GCP IAM / etc.)
Step 5  Write new secret to Vault:
        vault kv put secret/data/llm/anthropic_key value=<new_key>
Step 6  Issue new AppRole secret_id (Vault Agent picks up on next renewal)
Step 7  Verify: run smoke test — service can authenticate and reach its dependency
Step 8  Record: create audit event type audit.secret_rotated in the immutable trail (ADR-0024)
```

RTO for emergency revocation: < 30 seconds for steps 2–3 (per ADR-0025).
Full rotation (steps 4–7) target: < 15 minutes.

### 3.6 Prohibited patterns

The `secret-in-env` Semgrep rule (spec 13) blocks:

```python
# PROHIBITED — blocked by Semgrep rule secret-in-env
import os
api_key = os.environ["ANTHROPIC_API_KEY"]  # nosemgrep requires Security Lead sign-off

# PROHIBITED — blocked by Gitleaks (G06)
ANTHROPIC_API_KEY = "sk-ant-..."

# CORRECT — secrets read from Vault Agent tmpfs mount
with open("/vault/secrets/anthropic_key") as f:
    api_key = f.read().strip()
```

No `.env` files, no `secrets:` in Kubernetes manifests (except Vault Agent bootstrap),
no secrets in GitHub Actions `env:` blocks (use OIDC or Vault Action instead).

### 3.7 Privacy Impact

- Vault audit logs may contain accessor IDs and policy names but never secret values
  (`[REDACTED]` in all audit responses).
- Secret IDs are pseudonymous (Vault-generated UUIDs) — no PII.
- Vault audit logs are retained 2 years under the same policy as the application audit
  trail (ADR-0030), subject to the same erasure constraints (append-only).

---

## 4. Acceptance Criteria

- [ ] Secret catalogue lists all 8 secrets (S-01 to S-08) with Vault path, consumer and auth method
- [ ] Vault policy examples show minimum-privilege `read`-only capabilities per service
- [ ] Rotation schedule covers all secrets with interval, automation status and owner
- [ ] S-08 AppRole secret_id auto-renewed by Vault Agent with 1-hour TTL
- [ ] Emergency revocation procedure is 8 steps with RTO < 30s for revocation (steps 2–3)
- [ ] Prohibited patterns section shows the three anti-patterns blocked by Semgrep and Gitleaks
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                               |
| -------- | ----------------------------------------------------------------------- |
| ADR-0007 | PR merge gates — G06 (Gitleaks secret scan) enforces no secrets in repo |
| ADR-0020 | Zero-trust secrets management — Vault OSS, AppRole, sidecar             |
| ADR-0023 | HITL signing key (S-02) used by ApprovalToken HMAC validation           |
| ADR-0024 | Immutable audit trail — `audit.secret_rotated` event type               |
| ADR-0025 | Kill-switch — emergency revocation is step 3 of kill-switch protocol    |
| ADR-0030 | Data retention — Vault audit logs retained 2 years                      |

---

## References

- `docs/adr/ADR-0020-zero-trust-secrets-management.md`
- `docs/adr/ADR-0025-kill-switch-credential-revocation.md`
- `specs/security/13-sast-dast-policy.md` — `secret-in-env` Semgrep rule
- `infrastructure/vault/policies/` — Vault HCL policies (Phase 5)
