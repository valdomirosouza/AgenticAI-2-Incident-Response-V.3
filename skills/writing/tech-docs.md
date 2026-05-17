# Skill: Technical Documentation

**Domain**: writing
**Activation triggers**: Technical documentation, component docs, service docs, API docs, README, architecture documentation, C4 diagrams, tech spec, design doc
**References**: specs/system/01-system-architecture.md, ADR-0001, CLAUDE.md §2

---

## Principles

1. **Spec first** — no documentation artifact is authored without an approved spec (RULE-001).
2. **Derive from source** — all technical claims must trace back to code, an ADR, or a spec. Never document intent that is not implemented.
3. **English only** — all technical documentation is written in English (RULE-005).
4. **Audience-driven** — every document names its intended reader in the opening line.

---

## Document Types and When to Use Each

| Document type        | When to use                                                             | Template section |
| -------------------- | ----------------------------------------------------------------------- | ---------------- |
| **Component README** | Every `src/` subdirectory that exposes a public interface               | §1               |
| **Architecture doc** | C4 Level 1 or Level 2 change; new system boundary or major data flow    | §2               |
| **Runbook**          | New agent capability, new remediation action type, or on-call procedure | §3               |
| **ADR**              | Any architectural decision (see CLAUDE.md §6 for trigger list)          | `adr-template`   |
| **Spec**             | Any new system contract before implementation begins                    | `spec-template`  |
| **API reference**    | Any HTTP endpoint or agent message type exposed to callers              | §4               |

---

## Section 1: Component README Template

```markdown
# <ComponentName>

**Layer**: [domain | application | adapters/inbound | adapters/outbound | infrastructure]
**Autonomy**: [HITL | HOTL | N/A]
**Owner**: <role>

## Responsibility

One-paragraph description of what this component does and what it does NOT do.

## Interface

### Inputs

| Name    | Type  | Source                  | PII risk |
| ------- | ----- | ----------------------- | -------- |
| `field` | `str` | Kafka topic / REST POST | [yes/no] |

### Outputs

| Name         | Type  | Destination             | Audit event written |
| ------------ | ----- | ----------------------- | ------------------- |
| `event_type` | `str` | Audit trail + PagerDuty | `incident.created`  |

## Guardrails Applied

List each guardrail pattern (from `domain/guardrails-patterns.md`) that this component uses.

## Configuration

| Env var     | Default | Description                         |
| ----------- | ------- | ----------------------------------- |
| `LLM_MODEL` | —       | LLM model ID (required, no default) |

## Tests

| Layer       | Location                         | Coverage target |
| ----------- | -------------------------------- | --------------- |
| Unit        | `tests/unit/<component>/`        | ≥ 80%           |
| Integration | `tests/integration/<component>/` | ≥ 60%           |

## Related Specs and ADRs

- Spec: `specs/<domain>/<NN>-<name>.md`
- ADRs: ADR-XXXX
```

---

## Section 2: Architecture Documentation (C4 Model — ADR-0001)

All architecture diagrams follow the C4 Model. Use ASCII art for Markdown-native
rendering; Mermaid is acceptable for tooling that renders it.

### C4 Level 1 — System Context

```
[External system / user] --> [System being documented] --> [External dependency]
```

Mandatory elements:

- System name and one-line description
- All external users (roles, not individuals)
- All external systems with data flow direction
- Trust boundaries (dashed box)

### C4 Level 2 — Container Diagram

Each container = deployable unit (service, database, queue). For each:

| Field              | Required content                               |
| ------------------ | ---------------------------------------------- |
| **Name**           | Service name matching `src/` directory         |
| **Technology**     | Language + framework                           |
| **Responsibility** | ≤ 2 sentences                                  |
| **Communication**  | Protocol + direction (sync REST / async Kafka) |
| **PII handling**   | Does it process PII? Masking applied?          |

### C4 Level 3 — Component (use sparingly)

Only for components with non-obvious internal structure. Reference `specs/system/01-system-architecture.md` AC-01–AC-06 import rules.

---

## Section 3: Runbook Template

````markdown
# Runbook: <Title>

**Incident type**: [availability | latency | error_rate | saturation]
**Severity applicability**: [P1 | P2 | P3 | P4]
**Autonomy**: [HITL — requires ApprovalToken | HOTL — auto with override]
**RTO target**: < N minutes

## Trigger Conditions

Describe the exact metric/alert condition that activates this runbook.

## Diagnosis Steps

1. Check `<metric_name>` in Grafana dashboard `<dashboard-name>`.
2. Query Loki: `{service="<svc>"} |= "error" | json`.
3. ...

## Remediation Actions

### Option A — <ActionName> (Confidence: High)

**Action type**: `PRODUCTION_<type>`
**HITL required**: Yes — submit via `POST /incidents/{id}/remediation/approve`

```shell
# Command or API call
```
````

**Expected outcome**: Describe what returns to normal.
**Rollback**: Describe undo procedure.

## Escalation

If no resolution in <N> minutes, escalate to Engineering Lead via `POST /incidents/{id}/escalate`.

## Post-mortem Trigger

File a post-mortem if MTTR > <N> minutes or if remediation was `UNKNOWN_REMEDIATION`.

````

---

## Section 4: API Reference Template

Document every HTTP endpoint and every `AgentMessage` type.

### HTTP Endpoint

```markdown
### POST /incidents/{id}/remediation/approve

**Auth**: Bearer token (role: `on_call_engineer` or `engineering_lead`)
**HITL gate**: Issues an ApprovalToken (ADR-0023)

#### Request body

```json
{
  "action_type": "PRODUCTION_scale_replicas",
  "approver_role": "on_call_engineer",
  "justification": "string"
}
````

#### Response 200

```json
{
  "token_id": "uuid",
  "expires_at": "ISO-8601"
}
```

#### Error responses

| Status | Code                    | Meaning                                      |
| ------ | ----------------------- | -------------------------------------------- |
| 400    | `action_type_mismatch`  | Token action does not match proposed action  |
| 403    | `unauthorised_approver` | Caller role not in AUTHORISED_APPROVER_ROLES |
| 410    | `token_expired`         | Token TTL exceeded                           |

```

### AgentMessage Type

Reference `specs/system/02-agent-design.md` for the canonical Pydantic schema.
All new message types must be added to that spec before implementation.

---

## Quality Checklist

Before marking a documentation artifact as done:

- [ ] Audience named in opening paragraph
- [ ] All claims trace to code, ADR, or spec (no undocumented intent)
- [ ] No PII in examples — use role labels (`engineer_alpha`) or synthetic data
- [ ] No secrets or real hostnames — use `[REDACTED_HOST]` placeholders
- [ ] English only (RULE-005)
- [ ] Runbook includes rollback and escalation paths
- [ ] API reference includes all error responses
- [ ] Architecture doc names trust boundaries and PII flows
- [ ] Doc harness gate (`harness/doc-check.yml`) passes
```
