# Skill: Testing

**Domain**: sdlc
**Activation triggers**: Testing, test strategy, test pyramid, unit test, integration test, e2e test, coverage, pytest, fixtures, TDD, test coverage threshold, guardrail testing
**References**: specs/sdlc/04-definition-of-done.md, ADR-0008, CLAUDE.md §5.3 RULE-C02

---

## Test Pyramid

```
            ┌──────────┐
            │   E2E    │  ← few; full incident lifecycle; staging only
            ├──────────┤
            │Integration│ ← real DB/queue/Vault; no mocks for infra
            ├──────────┤
            │   Unit   │  ← many; pure functions; fast; mocks for ports
            └──────────┘
```

| Layer       | Location                 | Coverage target  | Mocking policy                               |
| ----------- | ------------------------ | ---------------- | -------------------------------------------- |
| Unit        | `tests/unit/`            | ≥ 80%            | Mock all ports/adapters; pure domain         |
| Integration | `tests/integration/`     | ≥ 60%            | Real infra (real DB, real Vault); no mock DB |
| E2E         | `tests/e2e/`             | Key paths only   | Full stack in staging; no mocks              |
| Security    | `tests/security/`        | All OWASP checks | DAST fixtures; prompt injection tests        |
| Guardrails  | `tests/unit/guardrails/` | **≥ 95% branch** | Dedicated; must test failure paths           |

> ADR-0008: integration tests must hit a real database and real Vault — mock divergence caused a prod migration failure. No exceptions.

---

## Coverage Thresholds (ADR-0008)

| Scope               | Threshold    | Gate | Measurement                                                       |
| ------------------- | ------------ | ---- | ----------------------------------------------------------------- |
| Overall unit        | ≥ 80%        | G01  | `pytest --cov=src tests/unit/`                                    |
| Overall integration | ≥ 60%        | G02  | `pytest --cov=src tests/integration/`                             |
| `src/guardrails/`   | ≥ 95% branch | G03  | `pytest --cov=src/guardrails --cov-branch tests/unit/guardrails/` |

---

## Fixture Rules (RULE-C02)

- Test fixtures must use **real data from included papers (P1–P19+)** for research scripts, not synthetic data.
- Application fixtures use **anonymised** incident data (k ≥ 5, re-ID risk < 5%) — never raw PII.
- No real usernames, IPs, or service names — use role labels (`engineer_alpha`) and `svc_<cat>_<N>` (spec 22).
- No secrets or API keys in fixtures — use environment variables or Vault test mounts.

---

## Guardrail Testing Requirements

Each guardrail must have tests asserting the **failure path** (the happy path is insufficient):

| Guardrail        | Required negative test                                                                       |
| ---------------- | -------------------------------------------------------------------------------------------- |
| HITL gate        | Assert no production action taken when token is missing, expired, or wrong type              |
| PII sanitizer    | Assert `PiiSanitizationRequired` raised when `sanitized=False`                               |
| Schema validator | Assert `LLMOutputInvalid` raised on malformed LLM output                                     |
| Confidence gate  | Assert low-confidence label injected when score < 0.6                                        |
| Kill-switch      | Assert Vault revocation and `sys.exit` called; audit event written                           |
| HOTL hook        | Assert notification sent even when action succeeds; action not blocked if notification fails |

```python
# Example: HITL gate negative test
def test_execute_raises_without_token():
    with pytest.raises(TypeError):
        action_executor.execute(action=some_action)  # no token argument

def test_execute_raises_on_expired_token(expired_token, some_action):
    with pytest.raises(HITLValidationError, match="token_expired"):
        action_executor.execute(action=some_action, token=expired_token)

def test_execute_raises_on_action_type_mismatch(valid_token, mismatched_action):
    with pytest.raises(HITLValidationError, match="action_type_mismatch"):
        action_executor.execute(action=mismatched_action, token=valid_token)
```

---

## Agent Testing Patterns

### Unit testing an agent use case

```python
# tests/unit/agents/test_triage_agent.py
from unittest.mock import MagicMock
from src.application.use_cases.classify_severity import ClassifySeverityUseCase

def test_classify_p1_on_high_error_rate():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = '{"severity": "P1", "confidence": 0.92, ...}'
    mock_audit = MagicMock()

    use_case = ClassifySeverityUseCase(llm=mock_llm, audit=mock_audit)
    result = use_case.execute(incident_id="inc-2026-0501-001", metrics=p1_metrics_fixture)

    assert result.severity == "P1"
    mock_audit.write.assert_called_once()  # audit event written
    assert mock_llm.complete.call_args.kwargs["sanitized"] is True  # PII gate
```

### Integration testing with real Vault

```python
# tests/integration/guardrails/test_hitl_gate_integration.py
# Uses real Vault dev server — no mock
def test_token_validation_with_real_vault(vault_client, signing_key_in_vault):
    token = create_approval_token(signing_key=vault_client.get_secret("hitl/signing_key"))
    validate_token(token, vault_client.get_secret("hitl/signing_key"))  # must not raise
```

---

## Research Script Testing (RULE-C01)

Every analysis script must have a docstring citing the RQ it supports:

```python
def compute_mttd(df: pd.DataFrame) -> pd.Series:
    """RQ1: MTTD per incident. Timestamps rounded to minute for k-anonymity."""
    return (df["t1_detection"] - df["t0_onset"]).dt.total_seconds() / 60
```

Test fixtures for research scripts use **real data from included papers** — not synthetic (RULE-C02).

---

## Test Naming Convention

```
test_<what>_<condition>_<expected_outcome>

Examples:
  test_validate_token_expired_raises_hitl_validation_error
  test_sanitize_with_cpf_masks_pii
  test_classify_severity_low_confidence_injects_label
  test_kill_switch_revokes_vault_credentials
```

---

## Running Tests Locally

```shell
# Unit tests with coverage
pytest --cov=src --cov-report=term-missing tests/unit/

# Guardrails with branch coverage
pytest --cov=src/guardrails --cov-branch --cov-fail-under=95 tests/unit/guardrails/

# Integration (requires running services — use docker-compose.test.yml)
pytest tests/integration/

# All (CI equivalent)
pytest --cov=src --cov-branch tests/unit/ tests/integration/
```
