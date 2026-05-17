# Skill: Guardrails Patterns

**Domain**: domain
**Activation triggers**: Guardrails, HITL implementation, HOTL, kill-switch, rollback triggers, agent safety, autonomy controls, ApprovalToken
**References**: specs/ethics/16-autonomy-boundaries.md, ADR-0023, ADR-0025, ADR-0021

---

## What Is a Guardrail?

A **guardrail** is an executable technical control that constrains or validates agent
actions. It is not a policy document — it is code that runs at agent decision time and
either permits, rejects or transforms the action.

Guardrails operate at three layers (defence in depth):

| Layer        | Mechanism                                  | Example                                                |
| ------------ | ------------------------------------------ | ------------------------------------------------------ |
| **Input**    | Validate/sanitize what enters the agent    | Presidio PII sanitization before LLM prompt (ADR-0028) |
| **Decision** | Validate the action before execution       | ApprovalToken HITL gate (ADR-0023)                     |
| **Output**   | Validate/constrain what the agent produces | Pydantic schema validation on LLM response (ADR-0021)  |

---

## Pattern 1: HITL Gate (ApprovalToken)

Use when: agent wants to execute any `PRODUCTION_*` action.

```python
# src/guardrails/hitl_gate.py
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID
import hmac, hashlib

@dataclass(frozen=True)
class ApprovalToken:
    token_id: UUID
    incident_id: str
    action_type: str        # must match the PRODUCTION_* action being approved
    approver_role: str
    approved_at: datetime
    expires_at: datetime
    signature: str          # HMAC-SHA256 over canonical fields

def validate_token(token: ApprovalToken, signing_key: bytes) -> None:
    """Raises HITLValidationError on any failure — never returns silently."""
    # 1. Verify signature
    canonical = f"{token.token_id}|{token.incident_id}|{token.action_type}|{token.approved_at.isoformat()}"
    expected_sig = hmac.new(signing_key, canonical.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(token.signature, expected_sig):
        raise HITLValidationError("signature_invalid")

    # 2. Check expiry
    if datetime.now(timezone.utc) > token.expires_at:
        raise HITLValidationError("token_expired")

    # 3. Check action type matches
    # (caller passes the action they intend to execute)
    pass  # action_type checked by action_executor before calling validate_token

    # 4. Check approver role is authorised
    if token.approver_role not in AUTHORISED_APPROVER_ROLES:
        raise HITLValidationError("unauthorised_approver")


# src/adapters/outbound/action_executor.py
def execute(action: ProductionAction, token: ApprovalToken) -> ActionResult:
    """Only entry point for PRODUCTION_* actions. No token = no execution."""
    if token.action_type != action.action_type:
        raise HITLValidationError("action_type_mismatch")

    signing_key = vault.get_secret("hitl/signing_key")
    validate_token(token, signing_key)           # raises on any failure

    audit.write(AuditEvent(event_type="remediation.executed", ...))
    return adapter.execute(action)
```

**Key invariants:**

- `execute()` is the **only** code path that runs `PRODUCTION_*` actions.
- No default value for `token` — callers must explicitly provide one.
- Any `HITLValidationError` → action not executed; audit event `hitl.validation_failed` written.
- Semgrep rule `hitl-bypass` detects any call to `adapter.execute()` that bypasses `action_executor`.

---

## Pattern 2: HOTL Monitoring Hook

Use when: agent acts automatically but must surface the decision for human review.

```python
# src/guardrails/hotl_hook.py
from typing import TypeVar, Callable, Any

T = TypeVar("T")

def hotl_action(
    action_fn: Callable[..., T],
    notify_fn: Callable[[str, Any], None],
    description: str,
    *args, **kwargs
) -> T:
    """Execute action and notify on-call; human may override via API."""
    result = action_fn(*args, **kwargs)
    notify_fn(
        channel="on-call",
        message=f"[AI-GENERATED] {description} — override at /incidents/{kwargs.get('incident_id')}"
    )
    audit.write(AuditEvent(event_type=kwargs.get("event_type"), ...))
    return result

# Usage in TriageAgent:
severity = hotl_action(
    action_fn=classify_severity,
    notify_fn=pagerduty.notify,
    description=f"Severity classified as {result.severity} (confidence {result.confidence:.0%})",
    incident_id=incident_id,
    event_type="incident.severity_set",
    metrics=current_metrics
)
```

**Key invariants:**

- Result is always returned regardless of notification success.
- Override endpoint `POST /incidents/{id}/severity` must be live before the HOTL fires.
- Notification failure → log warning, do not block the action.

---

## Pattern 3: PII Sanitization Gate

Use when: any text is about to be sent to an external LLM API.

```python
# src/guardrails/pii_sanitizer.py
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def sanitize(text: str) -> str:
    """Must be called before every LLMAdapter.complete() call."""
    results = analyzer.analyze(text=text, language="pt")
    results += analyzer.analyze(text=text, language="en")
    results += _regex_pass(text)          # CPF, CNPJ, IPv6, BR phone

    if results:
        audit.write(AuditEvent(
            event_type="pii.masked",
            payload={"entity_types": [r.entity_type for r in results], "count": len(results)}
        ))

    return anonymizer.anonymize(text=text, analyzer_results=results).text


# src/adapters/outbound/llm_adapter.py
def complete(self, prompt: str, *, sanitized: bool = False) -> str:
    if not sanitized:
        raise PiiSanitizationRequired(
            "Call pii_sanitizer.sanitize(prompt) and pass sanitized=True."
        )
    return self._client.messages.create(...)
```

**Key invariants:**

- `sanitized=True` is a **convention enforced by Semgrep** (`llm-unsanitized-prompt` rule) — not a cryptographic proof.
- Presidio confidence threshold: 0.7 (configurable in `pii_sanitizer_config.py`).
- False negatives are accepted risk — documented in DPIA/RIPD (spec 21, R-09).

---

## Pattern 4: Schema Validation Gate (LLM Output)

Use when: an LLM response is received and must be used in agent logic.

```python
# src/guardrails/schema_validator.py
from pydantic import BaseModel, ValidationError

class RCAHypothesis(BaseModel):
    root_cause: str
    confidence: float           # 0.0 – 1.0
    contributing_factors: list[str]
    recommended_actions: list[str]

def validate_llm_response(raw: str, schema: type[BaseModel]) -> BaseModel:
    try:
        return schema.model_validate_json(raw)
    except ValidationError as e:
        audit.write(AuditEvent(event_type="llm.schema_validation_failed", payload={"errors": str(e)}))
        raise LLMOutputInvalid(f"LLM response did not match schema: {e}") from e
        # Caller must escalate — never guess or use raw string
```

**Key invariants:**

- `LLMOutputInvalid` → caller escalates to on-call, does not attempt to parse raw text.
- Schema validation failure increments `llm_schema_validation_failures_total` metric.
- If failure rate > 5% → P2 alert (spec 11 on-call trigger).

---

## Pattern 5: Kill-Switch

Use when: the agent must be stopped immediately (runaway action, security incident,
operator command).

```python
# src/guardrails/kill_switch.py
import signal, sys

class KillSwitch:
    def __init__(self, vault_client, audit_port):
        self._vault = vault_client
        self._audit = audit_port

    def activate(self, reason: str) -> None:
        """RTO target: pod termination < 10s, credential revocation < 30s."""
        self._audit.write(AuditEvent(
            event_type="agent.kill_switch_activated",
            payload={"reason": reason}
        ))

        # Step 1: Revoke all Vault AppRole secret_ids (< 30s)
        self._vault.revoke_prefix("auth/approle/")
        self._vault.revoke_prefix("secret/data/llm/")
        self._vault.revoke_prefix("secret/data/hitl/")

        # Step 2: Terminate process (pod restarts with no active leases)
        sys.exit(1)                          # Kubernetes restarts pod; new secret_id required

# Register SIGTERM handler (Kubernetes sends SIGTERM before SIGKILL)
switch = KillSwitch(vault, audit)
signal.signal(signal.SIGTERM, lambda *_: switch.activate("SIGTERM received"))
```

**Automatic triggers** (OrchestratorAgent monitors these):

- Audit trail write failure (any occurrence) → P1
- Two consecutive remediation failures for the same incident
- `agent.kill_switch_activated` loop detected (re-activation within 60s)

**RTO targets (ADR-0025):**

- Pod termination: < 10 seconds
- Vault credential revocation: < 30 seconds (concurrent with pod termination)
- Full kill-switch RTO: < 60 seconds

---

## Pattern 6: Confidence Threshold Gate

Use when: an agent output carries a confidence score and should not be used below a
minimum threshold.

```python
# src/guardrails/confidence_gate.py
MIN_CONFIDENCE = 0.6   # from ADR-0021 (OWASP LLM09 overreliance mitigation)

def check_confidence(result: RCAHypothesis, incident_id: str) -> RCAHypothesis:
    if result.confidence < MIN_CONFIDENCE:
        audit.write(AuditEvent(
            event_type="rca.confidence_low",
            payload={"confidence": result.confidence, "threshold": MIN_CONFIDENCE}
        ))
        # Surface with warning label rather than blocking — HOTL pattern
        result = result.model_copy(update={
            "root_cause": f"[LOW CONFIDENCE: {result.confidence:.0%}] {result.root_cause}"
        })
    return result
```

---

## Guardrail Composition

All guardrails compose in a pipeline — never skip a layer:

```
User/external input
      │
      ▼ [INPUT] PII sanitization gate (Pattern 3)
      │
      ▼ [DECISION] HITL gate (Pattern 1) — if PRODUCTION_* action
         HOTL hook (Pattern 2) — if informational action
      │
      ▼ [OUTPUT] Schema validation gate (Pattern 4)
         Confidence threshold gate (Pattern 6)
      │
      ▼ Audit event written (always, before and after)
      │
      ▼ Kill-switch (Pattern 5) — emergency path, always available
```

---

## Testing Guardrails

Each guardrail must have dedicated unit tests asserting the failure path:

| Guardrail        | Required test                                                                             |
| ---------------- | ----------------------------------------------------------------------------------------- |
| HITL gate        | Assert no production action taken when token is missing, expired or has wrong action_type |
| PII sanitizer    | Assert `PiiSanitizationRequired` raised when `sanitized=False`                            |
| Schema validator | Assert `LLMOutputInvalid` raised on malformed LLM output                                  |
| Confidence gate  | Assert low-confidence label injected when score < 0.6                                     |
| Kill-switch      | Assert Vault revocation and sys.exit called; audit event written                          |

Coverage target for guardrails module: **≥ 95% branch coverage** (ADR-0008).
