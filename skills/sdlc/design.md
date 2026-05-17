# Skill: Design

**Domain**: sdlc
**Activation triggers**: System design, architecture review, design decision, component design, interface design, C4 diagram, hexagonal architecture, data flow, ADR needed
**References**: specs/system/01-system-architecture.md, ADR-0001, ADR-0002, CLAUDE.md §6

---

## Design Principles

1. **Hexagonal Architecture** — domain layer has zero imports from adapters or infrastructure (ADR-0002). Enforced by import-linter at G13.
2. **C4 Model** for all architecture documentation — Level 1 (context), Level 2 (container), Level 3 (component, sparingly) (ADR-0001).
3. **Decision before design** — any design choice that constitutes an architectural decision generates an ADR before the design is finalized.
4. **PII boundaries explicit** — every design diagram that crosses a trust boundary labels the PII categories in transit.
5. **HITL/HOTL explicit** — every component interaction involving agent actions labels the autonomy level.

---

## Layer Import Rules (ADR-0002)

```
infrastructure/          ← can import: adapters, application, domain
adapters/inbound/        ← can import: application, domain
adapters/outbound/       ← can import: application, domain
application/             ← can import: domain only
domain/                  ← NO external imports; only stdlib + pydantic
```

| Rule  | Constraint                                                           | Enforced by         |
| ----- | -------------------------------------------------------------------- | ------------------- |
| AC-01 | `domain/` must not import from `adapters/` or `infrastructure/`      | import-linter (G13) |
| AC-02 | `application/` must not import from `adapters/` or `infrastructure/` | import-linter       |
| AC-03 | `adapters/inbound/` must not import from `adapters/outbound/`        | import-linter       |
| AC-04 | All cross-layer calls via interfaces defined in `domain/ports/`      | Code review         |
| AC-05 | No circular imports between any two modules                          | import-linter       |
| AC-06 | `guardrails/` treated as `domain/` layer — same restrictions         | import-linter       |

---

## Design Review Checklist

Before opening a design PR or finalizing a component design:

### Architecture

- [ ] C4 Level 2 diagram updated if a new container or significant data flow is added
- [ ] Trust boundaries identified and labeled
- [ ] PII flows labeled with PII categories (from `specs/privacy/19-pii-inventory.md`)
- [ ] Import layer rules (AC-01–AC-06) respected
- [ ] No circular dependencies introduced

### Agent design

- [ ] Agent autonomy level (HITL / HOTL / BLOCKED) documented for each action type
- [ ] Agent actions reference `specs/ethics/16-autonomy-boundaries.md` matrix
- [ ] `AgentMessage` Pydantic schema defined for new message types (spec 02)
- [ ] Orchestrator FSM state transitions updated if new agent states added

### Guardrails

- [ ] All new `PRODUCTION_*` action types go through `action_executor` (HITL gate)
- [ ] New HOTL actions include `notify_fn` call
- [ ] Schema validation applied to all new LLM response paths
- [ ] PII sanitization applied before any new LLM prompt construction

### Data

- [ ] New data stores include retention TTL (spec 20)
- [ ] PII in new data stores classified per spec 19
- [ ] New cross-boundary data flows added to DPIA/RIPD (spec 21) if PII present

---

## ADR Trigger Checklist

Create an ADR when the design introduces:

| Trigger                                    | ADR covers                                     |
| ------------------------------------------ | ---------------------------------------------- |
| New external service or library dependency | Selection rationale, alternatives, trade-offs  |
| New PRODUCTION\_\* action type             | Autonomy classification, HITL enforcement      |
| New PII category or data store             | Legal basis, retention, masking approach       |
| Change to hexagonal layer boundaries       | Import rules update, migration path            |
| New LLM model or provider                  | Model selection, cost, risk, OWASP LLM mapping |
| Change to the audit trail schema           | Backward compatibility, migration              |
| New test coverage threshold                | Rationale, impact on CI                        |

---

## Interface Design Patterns

### Port (domain layer — defines the contract)

```python
# src/domain/ports/outbound/llm_port.py
from abc import ABC, abstractmethod

class LLMPort(ABC):
    @abstractmethod
    def complete(self, prompt: str, *, sanitized: bool) -> str:
        """Caller must pass sanitized=True — enforced by Semgrep rule llm-unsanitized-prompt."""
```

### Adapter (implements the port — outside domain layer)

```python
# src/adapters/outbound/llm_adapter.py
from src.domain.ports.outbound.llm_port import LLMPort

class AnthropicAdapter(LLMPort):
    def complete(self, prompt: str, *, sanitized: bool = False) -> str:
        if not sanitized:
            raise PiiSanitizationRequired(...)
        return self._client.messages.create(...)
```

### Use case (application layer — orchestrates domain + ports)

```python
# src/application/use_cases/classify_severity.py
class ClassifySeverityUseCase:
    def __init__(self, llm: LLMPort, audit: AuditPort):
        self._llm = llm
        self._audit = audit

    def execute(self, incident_id: str, metrics: MetricSnapshot) -> SeverityResult:
        ...
```

---

## Component Sizing Guidelines

| Signal                             | Action                                             |
| ---------------------------------- | -------------------------------------------------- |
| Component has > 3 responsibilities | Split into two components with a port between them |
| Use case > 50 lines                | Extract domain service or strategy                 |
| Test file > 200 lines              | Split into focused test modules                    |
| Adapter calls 3+ external services | Introduce a facade or gateway component            |
