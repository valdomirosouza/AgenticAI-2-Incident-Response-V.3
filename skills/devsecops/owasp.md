# Skill: OWASP

**Domain**: devsecops
**Activation triggers**: OWASP, OWASP LLM Top 10, OWASP Web Top 10, prompt injection, LLM security, insecure output handling, supply chain, overreliance, LLM01, LLM02, LLM09
**References**: specs/security/12-threat-model.md, specs/security/13-sast-dast-policy.md, ADR-0017, ADR-0021

---

## OWASP LLM Top 10 — Project Applicability

Each risk is assessed against this project's architecture and mitigated accordingly.

| ID    | Risk                             | Applicability | Mitigation in this project                                                                     |
| ----- | -------------------------------- | ------------- | ---------------------------------------------------------------------------------------------- |
| LLM01 | Prompt Injection                 | **High**      | PII sanitizer strips attacker-controlled content; Pydantic schema rejects unexpected fields    |
| LLM02 | Insecure Output Handling         | **High**      | All LLM responses validated via `validate_llm_response()` before use; no raw output in actions |
| LLM03 | Training Data Poisoning          | Low           | No fine-tuning in this project; mitigated by model provider                                    |
| LLM04 | Model Denial of Service          | **Medium**    | Token budget gauge + alert; request timeout; rate limiting at API boundary                     |
| LLM05 | Supply Chain Vulnerabilities     | **High**      | Pinned model version + SHA in ADR-0003; pip-audit G11; CycloneDX SBOM                          |
| LLM06 | Sensitive Information Disclosure | **High**      | Presidio PII sanitization before every prompt (ADR-0028); forbidden span attributes            |
| LLM07 | Insecure Plugin Design           | **Medium**    | No external plugins; all tools are internal adapters with Pydantic input validation            |
| LLM08 | Excessive Agency                 | **Critical**  | HITL gate for all PRODUCTION\_\* actions; BLOCKED list enforced at 4 layers; kill-switch       |
| LLM09 | Overreliance                     | **High**      | Confidence threshold gate (MIN_CONFIDENCE = 0.6); low-confidence label surfaced to engineer    |
| LLM10 | Model Theft                      | Low           | Anthropic API — model not hosted locally; API key in Vault                                     |

---

## LLM01: Prompt Injection — Defense Patterns

**Risk**: attacker embeds instructions in incident data (log messages, alert titles) that manipulate agent behaviour.

```python
# VULNERABLE — raw log excerpt in prompt
prompt = f"Analyse this error: {log_excerpt}"

# MITIGATED — sanitize + bound the excerpt
sanitized_excerpt = pii_sanitizer.sanitize(log_excerpt[:2000])  # length bound
prompt = f"Analyse this error (sanitized excerpt):\n{sanitized_excerpt}"

# ALSO: validate LLM response against schema — ignore instructions in output
result = validate_llm_response(llm.complete(prompt, sanitized=True), RCAHypothesis)
```

**Additional controls:**

- Only log/trace **excerpts** are sent to LLM — not full dumps (spec 02)
- Pydantic schema validation rejects any response that attempts to add unexpected fields
- LLM cannot directly trigger PRODUCTION\_\* actions — it only returns a hypothesis/proposal

---

## LLM02: Insecure Output Handling — Defense Patterns

**Risk**: LLM output is used directly in agent logic without validation, enabling unexpected behaviour.

```python
# VULNERABLE — raw string used directly
raw = llm.complete(prompt, sanitized=True)
action_type = raw.split('"action_type": "')[1].split('"')[0]  # fragile parsing

# MITIGATED — Pydantic validation
result = validate_llm_response(raw, RemediationProposal)  # raises LLMOutputInvalid on failure
action_type = result.action_type  # typed, validated field
```

**Key invariant:** `LLMOutputInvalid` → escalate to on-call, never guess or use raw string.

---

## LLM08: Excessive Agency — Defense Patterns

**Risk**: agent autonomously executes high-impact actions without human approval.

```python
# BLOCKED — agent cannot call adapter.execute() directly
# (Semgrep rule hitl-bypass detects this pattern)
adapter.execute(scale_replicas_action)  # FORBIDDEN

# REQUIRED — must go through action_executor with valid token
token = await hitl_service.request_approval(action)   # blocks until human approves
action_executor.execute(action=scale_replicas_action, token=token)
```

**Architectural invariants (all enforced in parallel):**

1. `action_executor.execute()` is the only path — no bypass
2. No default value for `token` parameter
3. `BLOCKED` action types raise at domain model level before reaching executor
4. Semgrep rule G07 (`hitl-bypass`) catches direct `adapter.execute()` calls

---

## LLM09: Overreliance — Defense Pattern

**Risk**: system acts on low-confidence LLM output as if it were certain.

```python
# src/guardrails/confidence_gate.py
MIN_CONFIDENCE = 0.6  # ADR-0021: OWASP LLM09 overreliance mitigation

def check_confidence(result: RCAHypothesis, incident_id: str) -> RCAHypothesis:
    if result.confidence < MIN_CONFIDENCE:
        audit.write(AuditEvent(event_type="rca.confidence_low", ...))
        result = result.model_copy(update={
            "root_cause": f"[LOW CONFIDENCE: {result.confidence:.0%}] {result.root_cause}"
        })
    return result
```

**Key invariant:** low-confidence result is surfaced with a label — never silently dropped or promoted.

---

## OWASP Web Top 10 — API Boundary Checklist

Applied to the REST API (`src/api/`):

| Risk                          | Control                                                                    |
| ----------------------------- | -------------------------------------------------------------------------- |
| A01 Broken Access Control     | Bearer token required on all `/incidents/*` endpoints; role check          |
| A02 Cryptographic Failures    | TLS 1.2+ enforced; HMAC-SHA256 for ApprovalToken                           |
| A03 Injection                 | Pydantic input models on all request bodies; no raw SQL                    |
| A04 Insecure Design           | HITL gate architectural — cannot be disabled at runtime                    |
| A05 Security Misconfiguration | Vault for all secrets; no default credentials; headers hardened            |
| A06 Vulnerable Components     | pip-audit (G11); CycloneDX SBOM; Critical CVE 24h SLA                      |
| A07 Auth Failures             | ApprovalToken TTL + HMAC; failed attempts → `hitl.validation_failed` audit |
| A08 Data Integrity Failures   | SLSA Level 2 provenance; SHA-256 hash-pinned dependencies                  |
| A09 Logging Failures          | Audit trail write failure → P1 + kill-switch; 100% write SLO               |
| A10 SSRF                      | LLM API calls via Vault-managed credentials; no user-controlled URLs       |

---

## Manual OWASP LLM Checklist (spec 13)

Run during every PR review that touches agent code or LLM adapters:

- [ ] LLM01: No unsanitized external data in prompt construction
- [ ] LLM02: Every LLM response validated with `validate_llm_response()` before use
- [ ] LLM04: Token budget monitoring in place for new LLM call paths
- [ ] LLM06: No PII in prompt; `pii_sanitizer.sanitize()` called; `sanitized=True` passed
- [ ] LLM08: New action types classified HITL/HOTL/BLOCKED per spec 16
- [ ] LLM09: Confidence threshold gate applied to new output types
