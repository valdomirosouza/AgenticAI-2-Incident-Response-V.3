# ADR-0020: Zero-Trust Secrets Management — Vault Mandatory

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Security Lead — researcher)
**Affected RQs**: RQ1 (architecture), RQ4 (security compliance)

---

## Context

The Copilot requires secrets at runtime: Anthropic API key (ADR-0003), observability
backend credentials, database passwords, and inter-service mTLS certificates. Secrets
must be:

1. **Never stored in code or configuration files** — RULE-C03 prohibits credentials in
   the repository. SAST gate G03 (ADR-0007) enforces this at PR time.
2. **Never in environment variables baked into container images** — image inspection
   would expose them; image layers are immutable and cannot be rotated.
3. **Rotatable without redeployment** — LLM API keys and database passwords must be
   rotatable without a new container build or deployment cycle.
4. **Auditable** — every secret access must be logged: which service, which secret,
   which version, at what time. SOC 2 CC6 (Logical access controls) and CIS Controls
   v8 #14 (Security awareness and account management) require access auditability.
5. **Zero-trust model** — no service is implicitly trusted to access any secret. Each
   service must authenticate to the vault and receive only the secrets it is authorised
   to read (principle of least privilege).

## Decision

All secrets are managed via **HashiCorp Vault** (open-source) with **AppRole
authentication** for service-to-vault identity. No secret is stored in environment
variables, `.env` files, Kubernetes ConfigMaps, or any file tracked by git.

### Secrets taxonomy

| Secret category                   | Vault path                             | Rotation policy        |
| --------------------------------- | -------------------------------------- | ---------------------- |
| LLM API key (Anthropic)           | `secret/agents/llm/anthropic_api_key`  | 90 days                |
| Observability backend credentials | `secret/infra/observability/<backend>` | 90 days                |
| Database passwords                | `secret/infra/database/<service>`      | 30 days                |
| Inter-service mTLS certificates   | `pki/issue/<service>`                  | 30 days (auto-renewed) |
| HITL approval signing key         | `secret/agents/hitl/signing_key`       | 180 days               |

### Runtime secret injection

Secrets are injected at container startup via the **Vault Agent Sidecar** (Kubernetes)
or **Vault Agent** (local development):

```
Container start
     │
     ▼
Vault Agent (sidecar)
  ├── authenticate with AppRole (role_id + secret_id)
  ├── fetch secrets for this service's policy
  └── write to in-memory tmpfs at /vault/secrets/<name>
     │
     ▼
Application reads secret from /vault/secrets/<name>
(never from environment variable or disk)
```

In local development, `direnv` + `vault` CLI is used to inject secrets into the
process environment for the session only — never persisted to `.env` files.

### Vault technology selection

**HashiCorp Vault OSS** is selected over cloud-native alternatives because:

- Open-source: no cost for the research prototype; no vendor dependency for the
  dissertation replication package.
- Runs locally (dev mode) and on Kubernetes (production mode) — same tool across
  all environments.
- AppRole auth is well-documented and does not require a cloud IAM provider.

Cloud-native alternatives (AWS Secrets Manager, GCP Secret Manager) are viable for
a cloud deployment and do not require a separate infrastructure component. If the
research prototype moves to a managed cloud, a supplementary ADR documents the
migration.

### Prohibited patterns (enforced by SAST gate G03)

- `os.environ["ANTHROPIC_API_KEY"]` in application code
- `api_key = "sk-..."` in any file
- `env:` secrets in Kubernetes YAML without `secretKeyRef`
- `.env` files in the repository

## Alternatives Considered

| Alternative                         | Pros                                                                                                 | Cons                                                                                       |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| **Environment variables in `.env`** | Simple; widely used                                                                                  | Committed to git accidentally; not rotatable without redeployment; no audit log            |
| **Kubernetes Secrets**              | Built-in; no extra component                                                                         | Base64-encoded (not encrypted at rest by default); no audit log without additional tooling |
| **AWS Secrets Manager**             | Managed; auto-rotation; IAM integration                                                              | Cloud vendor lock-in; not reproducible without AWS account                                 |
| **HashiCorp Vault OSS** ✅          | Open-source; runs locally and on K8s; audit log built-in; zero-trust AppRole auth; no vendor lock-in | Adds an infrastructure component to manage; Vault is more complex than env vars            |

## Consequences

**Positive:**

- Zero secrets in git history — G03 gate enforces this at PR time; Vault audit log
  provides evidence for SOC 2 CC6 and CIS Controls #14.
- Rotation without redeployment: API key rotation only requires updating the Vault
  secret; running agents pick up the new value on next lease renewal.
- Zero-trust: each service authenticates with its own AppRole and can only read
  its own secrets — a compromised agent cannot read another agent's API keys.
- Local dev parity: `vault` CLI + `direnv` reproduces the same secret injection
  pattern as production — no "it works locally" vs. production divergence.

**Negative / Trade-offs:**

- Vault adds an infrastructure dependency that must be available before any agent
  service starts. In development, `vault server -dev` is used; CI uses a Vault
  container in the GitHub Actions service container.
- AppRole `secret_id` rotation requires operational discipline — documented in the
  secrets rotation runbook (`docs/runbooks/secrets-rotation.md`).

## Review Criteria

Revisit this decision if:

- The project moves to a managed cloud (GCP/AWS) and the cloud provider's secret
  manager offers sufficient audit and rotation features — document migration in a
  supplementary ADR.
- HashiCorp changes Vault's OSS licence in a way that is incompatible with the
  open dissertation replication package — evaluate OpenBao (OSS fork) as an alternative.

## References

- CIS Controls v8 #14 — Security Awareness and Skills Training; #18 — Penetration Testing
- SOC 2 Type II CC6 — Logical and physical access controls
- RULE-C03 (CLAUDE.md §5.3) — No sensitive data in repository
- `docs/adr/ADR-0007-pr-merge-gates-ci-checks.md` — gate G03 (secrets scan)
- `specs/security/14-secrets-management.md` — secrets management spec (to be authored, issue #12)
