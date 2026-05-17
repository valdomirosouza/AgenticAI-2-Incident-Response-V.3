# Skill: Secure Development

**Domain**: devsecops
**Activation triggers**: Secure development, threat modeling, security principles, secure coding, defense in depth, least privilege, input validation, secure by design, security architecture
**References**: specs/security/12-threat-model.md, ADR-0016, ADR-0017, CLAUDE.md §1.5

---

## Security Principles (applied to this project)

| Principle                | Application in this codebase                                                        |
| ------------------------ | ----------------------------------------------------------------------------------- |
| **Defense in depth**     | Guardrails at input + decision + output layers; HITL as final gate                  |
| **Least privilege**      | Vault AppRole policies grant minimum required paths; no wildcard policies           |
| **Fail secure**          | On any guardrail failure → raise exception, write audit event, never continue       |
| **Zero trust**           | Every agent message validated via Pydantic schema; no implicit trust between agents |
| **Separation of duties** | `action_executor` is the only path to PRODUCTION\_\* actions; no bypass             |
| **Auditability**         | Every agent decision writes an immutable audit event before and after action        |

---

## Trust Boundaries (spec 12)

Four trust boundaries govern what validation is required at each crossing:

| Boundary                       | Between                                    | Required controls                         |
| ------------------------------ | ------------------------------------------ | ----------------------------------------- |
| **External → Copilot**         | Internet / PagerDuty → Alert Consumer      | Input validation, rate limiting, auth     |
| **Copilot → LLM API**          | Agent → Anthropic API                      | PII sanitization (ADR-0028), TLS, API key |
| **Copilot → Production infra** | RemediationAgent → Kubernetes / cloud APIs | HITL gate (ADR-0023), HMAC token          |
| **Copilot → Observability**    | Any agent → Loki / Tempo / Prometheus      | PII masking (ADR-0014), no raw prompts    |

---

## STRIDE Threat Categories (spec 12)

| Threat category            | Examples in this system                          | Primary mitigation                              |
| -------------------------- | ------------------------------------------------ | ----------------------------------------------- |
| **Spoofing**               | Forged ApprovalToken; impersonated agent message | HMAC-SHA256 signature (ADR-0023)                |
| **Tampering**              | Modified audit event; manipulated LLM response   | SHA-256 hash chain (ADR-0024); Pydantic         |
| **Repudiation**            | Agent denies executing a remediation action      | Immutable audit trail (ADR-0024)                |
| **Information disclosure** | PII leaked in LLM prompt; credentials in logs    | Presidio sanitization; Gitleaks; ADR-0014       |
| **Denial of service**      | HITL queue flood; LLM token budget exhaustion    | Queue depth alert; token budget gauge           |
| **Elevation of privilege** | Agent bypasses HITL to execute BLOCKED action    | `action_executor` sole entry point; Semgrep G07 |

---

## Secure Coding Checklist

Apply before every code review of security-sensitive components.

### Input validation

- [ ] All external inputs validated against Pydantic model before use
- [ ] No dynamic SQL / shell / system calls constructed from user input
- [ ] `incident_id` format validated (`inc-YYYY-MMDD-NNN` pattern) before use as log label
- [ ] Alert payloads from PagerDuty/Prometheus validated against expected schema

### Secrets handling

- [ ] No secrets in source code, config files, or test fixtures (RULE-C03)
- [ ] All secrets accessed via `vault.get_secret("path/to/secret")`
- [ ] No secrets in environment variables that are logged
- [ ] `ANTHROPIC_API_KEY` and signing keys never appear in tracing attributes

### LLM security (OWASP LLM Top 10)

- [ ] Every LLM prompt passes `pii_sanitizer.sanitize()` before construction (ADR-0028)
- [ ] `LLMAdapter.complete()` called only with `sanitized=True`
- [ ] LLM response validated against Pydantic schema before use
- [ ] No direct execution of LLM-suggested code or commands
- [ ] Confidence threshold gate applied to all LLM outputs used in decisions

### HITL / guardrails

- [ ] `PRODUCTION_*` actions reachable only via `action_executor.execute()`
- [ ] No default value for `token` parameter in `execute()`
- [ ] `BLOCKED` action types checked at all four enforcement layers
- [ ] Kill-switch handler registered for SIGTERM

### Audit trail

- [ ] Audit event written **before** action and **after** action result
- [ ] `HITLValidationError` always writes `hitl.validation_failed` audit event
- [ ] No code path that calls `adapter.execute()` directly (Semgrep G07)

---

## Blocked Actions — Four Enforcement Layers

`PRODUCTION_data_delete`, `PRODUCTION_iam_change`, `PRODUCTION_firewall_change` are prohibited regardless of approval (spec 16):

| Layer             | Enforcement                                                    |
| ----------------- | -------------------------------------------------------------- |
| Domain model      | These action types raise `BlockedActionError` at instantiation |
| `action_executor` | Explicit check before token validation                         |
| API endpoint      | Returns `403 Forbidden` for blocked action types               |
| Semgrep rule      | `hitl-bypass` detects any code path that constructs these      |

---

## Security Review Triggers

Open a security-focused review (requires Security Lead + Tech Lead) when a PR:

- Adds a new `PRODUCTION_*` action type
- Modifies `action_executor.py`, `hitl_gate.py`, or `kill_switch.py`
- Changes the ApprovalToken schema or signing mechanism
- Modifies the audit trail write path
- Adds a new external dependency (supply chain risk)
- Changes PII handling in any observability component
- Modifies Vault policies or secret paths
