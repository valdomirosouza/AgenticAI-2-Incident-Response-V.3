# Spec 12: Threat Model

**Domain**: security
**Owner**: Security Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #12
**Linked ADRs**: ADR-0016
**Review cadence**: Every release + on CVE event or architecture change

---

## 1. Purpose

Define the STRIDE threat model for the Copilot — attack surface map, trust boundaries,
per-component threat register and mitigations inventory. This is the mandatory starting
point for secure design of every new component (ADR-0016).

---

## 2. Context

ADR-0016 adopted STRIDE with LLM-specific extensions (OWASP LLM Top 10) as the threat
modeling method. The Copilot presents a distinctive attack surface: it processes
observability data that may contain PII, constructs LLM prompts from that data, and
executes approved remediation actions against production infrastructure. Each of these
stages has distinct threat categories that standard STRIDE alone does not cover.

---

## 3. Decision

### 3.1 Trust boundary map

```
┌──────────────────────────────────────────────────────────────────────────┐
│  TRUST BOUNDARY 1: Kubernetes cluster namespace "copilot"                │
│                                                                          │
│  ┌─────────────┐    ┌─────────────────────────────────────────────────┐  │
│  │  API Layer  │    │  Agent Layer (OrchestratorAgent + Specialists)  │  │
│  │  (FastAPI)  │───►│  - No direct internet access                   │  │
│  └──────┬──────┘    │  - Vault sidecar only secret source            │  │
│         │           └──────────────────────┬────────────────────────┘  │
│         │                                  │                            │
└─────────┼──────────────────────────────────┼────────────────────────────┘
          │                                  │
          ▼ TB2                              ▼ TB3
┌─────────────────────┐        ┌──────────────────────────┐
│  TRUST BOUNDARY 2:  │        │  TRUST BOUNDARY 3:       │
│  External clients   │        │  External services       │
│  (On-call engineer, │        │  - Anthropic Claude API  │
│   PagerDuty/Slack)  │        │  - GitHub Actions        │
└─────────────────────┘        └──────────────────────────┘
          │                                  │
          ▼ TB4                              │
┌─────────────────────┐                     │
│  TRUST BOUNDARY 4:  │                     │
│  Observability ns   │◄────────────────────┘
│  (Prometheus, Loki, │  (metrics pull / log push)
│   Tempo, Grafana)   │
└─────────────────────┘
```

Data crossing trust boundaries must be sanitized (ADR-0028 at TB3, ADR-0014 at TB4).

### 3.2 Attack surface inventory

| Surface                         | Exposure           | Protocol | Auth mechanism                     |
| ------------------------------- | ------------------ | -------- | ---------------------------------- |
| REST API (`/incidents/*`)       | Internal cluster   | HTTPS    | mTLS + JWT (service account)       |
| HITL approval endpoint          | Internal cluster   | HTTPS    | mTLS + ApprovalToken (HMAC-SHA256) |
| Anthropic Claude API (outbound) | Internet (TB3)     | HTTPS    | API key via Vault                  |
| Observability scrape endpoints  | Namespace TB4      | HTTP     | NetworkPolicy restriction          |
| Vault sidecar (in-pod)          | Pod localhost only | HTTP     | AppRole token (TTL 1h)             |
| Audit trail store               | GCS object lock    | HTTPS    | Workload Identity                  |

### 3.3 STRIDE threat register

#### Component: API Layer (FastAPI)

| ID   | STRIDE category        | Threat                                                     | Likelihood | Impact   | Mitigation                                                   | Status    |
| ---- | ---------------------- | ---------------------------------------------------------- | ---------- | -------- | ------------------------------------------------------------ | --------- |
| T-01 | Spoofing               | Attacker impersonates on-call engineer to submit approvals | Low        | Critical | mTLS + HMAC-signed ApprovalToken (ADR-0023)                  | Mitigated |
| T-02 | Tampering              | Attacker modifies incident payload in transit              | Low        | High     | TLS in transit; JSON schema validation (Pydantic)            | Mitigated |
| T-03 | Repudiation            | Engineer denies submitting an approval                     | Low        | High     | Immutable audit trail with hash chain (ADR-0024)             | Mitigated |
| T-04 | Info Disclosure        | API response leaks PII from logs/traces                    | Medium     | High     | Presidio sanitization (ADR-0028); response schema validation | Mitigated |
| T-05 | Denial of Service      | Flood of fake incident creation requests                   | Medium     | Medium   | Rate limiting on API gateway; Kubernetes resource limits     | Partial   |
| T-06 | Elevation of Privilege | Non-admin submits remediation without approval             | Low        | Critical | `PiiSanitizationRequired`; HITL gate (ADR-0023)              | Mitigated |

#### Component: OrchestratorAgent + SpecialistAgents

| ID   | STRIDE category        | Threat                                            | Likelihood | Impact   | Mitigation                                                             | Status    |
| ---- | ---------------------- | ------------------------------------------------- | ---------- | -------- | ---------------------------------------------------------------------- | --------- |
| T-07 | Spoofing               | Malicious agent message spoofs a specialist agent | Low        | High     | Typed `AgentMessage` with `source_agent` field; in-process call graph  | Mitigated |
| T-08 | Tampering              | Audit event hash chain tampered post-write        | Low        | Critical | Append-only GCS object lock; SHA-256 chain (ADR-0024)                  | Mitigated |
| T-09 | Info Disclosure        | Agent logs contain raw PII                        | Medium     | High     | OTel SpanProcessor masks before emit (ADR-0014)                        | Mitigated |
| T-10 | Denial of Service      | Agent kill-switch not responding to termination   | Low        | High     | Kill-switch RTO < 60s; pod termination + Vault revocation (ADR-0025)   | Mitigated |
| T-11 | Elevation of Privilege | Agent bypasses HITL and executes PRODUCTION\_\*   | Low        | Critical | `validate_token_signature` in action_executor; Semgrep gate (ADR-0023) | Mitigated |

#### Component: LLM Interface (Anthropic Claude API)

| ID   | STRIDE category        | Threat                                                             | Likelihood | Impact   | Mitigation                                                                       | Status    |
| ---- | ---------------------- | ------------------------------------------------------------------ | ---------- | -------- | -------------------------------------------------------------------------------- | --------- |
| T-12 | LLM01 Prompt Injection | Attacker embeds instructions in log data to hijack agent behaviour | Medium     | Critical | Presidio sanitization (ADR-0028); structured output + Pydantic schema            | Mitigated |
| T-13 | LLM06 Info Disclosure  | LLM reproduces PII from prompt in response                         | Low        | High     | PII stripped before prompt (ADR-0028); response schema validation                | Mitigated |
| T-14 | LLM05 Improper Output  | LLM returns free-form text instead of schema                       | Medium     | High     | Pydantic validation; failure → escalate, not proceed (ADR-0021)                  | Mitigated |
| T-15 | Tampering              | API key for Anthropic rotated/stolen mid-session                   | Low        | High     | API key in Vault TTL lease; kill-switch revokes instantly (ADR-0025)             | Mitigated |
| T-16 | Info Disclosure        | Raw prompt cached or logged by the adapter                         | Low        | High     | `LLMAdapter` must not log prompt content; LLM prompts never persisted (ADR-0030) | Mitigated |

#### Component: Observability Pipeline

| ID   | STRIDE category   | Threat                                                  | Likelihood | Impact | Mitigation                                                                 | Status    |
| ---- | ----------------- | ------------------------------------------------------- | ---------- | ------ | -------------------------------------------------------------------------- | --------- |
| T-17 | Info Disclosure   | PII in metric labels exported to Prometheus             | Medium     | High   | No PII in label values enforced by OTel Collector processor (ADR-0014)     | Mitigated |
| T-18 | Info Disclosure   | PII in log lines shipped to Loki                        | Medium     | High   | Presidio scan in OTel SpanProcessor + Loki pipeline processor (ADR-0014)   | Mitigated |
| T-19 | Tampering         | Prometheus scrape endpoint poisoned with false metrics  | Low        | Medium | NetworkPolicy restricts scrape to observability namespace only             | Mitigated |
| T-20 | Denial of Service | Cardinality explosion in Prometheus from dynamic labels | Medium     | Medium | Label cardinality enforced in spec 08; Loki label set ≤ 3 labels (spec 09) | Mitigated |

### 3.4 Residual risks

| ID   | Threat                                    | Residual risk | Acceptance rationale                                                                                |
| ---- | ----------------------------------------- | ------------- | --------------------------------------------------------------------------------------------------- |
| T-05 | API DoS flood                             | Low-Medium    | Rate limiting is partial; full WAF out of scope for research prototype                              |
| T-12 | Novel prompt injection bypassing Presidio | Low           | Presidio false negatives documented in DPIA/RIPD (ADR-0029); defence-in-depth via schema validation |

All other threats are fully mitigated. No unmitigated Critical or High residual risks.

### 3.5 Threat model review triggers

This spec must be updated when:

- A new agent or external service is added (new trust boundary or attack surface)
- A new OWASP LLM Top 10 edition is published
- A CVE is identified in a dependency used at a trust boundary
- The HITL/HOTL configuration changes

---

## 4. Acceptance Criteria

- [ ] Trust boundary map covers all 4 boundaries: cluster, external clients, external services, observability
- [ ] Attack surface inventory lists all 6 exposed surfaces with auth mechanism
- [ ] STRIDE threat register covers 4 components: API layer, agents, LLM interface, observability pipeline
- [ ] All Critical and High threats have status "Mitigated" with ADR reference
- [ ] Residual risks section documents accepted partial mitigations with rationale
- [ ] No unmitigated Critical or High residual risks
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                             |
| -------- | --------------------------------------------------------------------- |
| ADR-0014 | PII masking — mitigates T-17, T-18 (observability PII disclosure)     |
| ADR-0016 | STRIDE + LLM extensions — threat modeling method                      |
| ADR-0020 | Vault — secret storage mitigating T-15 (API key exposure)             |
| ADR-0021 | OWASP LLM Top 10 — LLM-specific threats T-12, T-13, T-14              |
| ADR-0023 | HITL enforcement — mitigates T-01, T-06, T-11 (privilege escalation)  |
| ADR-0024 | Immutable audit trail — mitigates T-03, T-08 (repudiation, tampering) |
| ADR-0025 | Kill-switch — mitigates T-10, T-15 (DoS, credential compromise)       |
| ADR-0028 | PII sanitization — mitigates T-04, T-09, T-12, T-13, T-16             |
| ADR-0029 | DPIA/RIPD — residual risk T-12 documented in risk register            |
| ADR-0030 | Data retention — mitigates T-16 (prompts never persisted)             |

---

## References

- CLAUDE.md §1.5 Compliance Baseline (OWASP LLM Top 10, ISO 27001)
- `docs/adr/ADR-0016-stride-threat-modeling-method.md`
- `docs/adr/ADR-0021-owasp-llm-top10-checklist.md`
- `specs/system/01-system-architecture.md` — container diagram (DFD basis)
- `specs/security/13-sast-dast-policy.md` — automated threat detection
