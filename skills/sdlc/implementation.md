# Skill: Implementation

**Domain**: sdlc
**Activation triggers**: Coding standards, commit convention, branch strategy, implementation, code style, naming, Conventional Commits, trunk-based development, Python standards
**References**: specs/sdlc/05-branching-strategy.md, ADR-0005, ADR-0006, CLAUDE.md §5.3

---

## Branching Strategy (ADR-0005 — trunk-based development)

| Branch pattern            | Purpose                                        | Lifetime       |
| ------------------------- | ---------------------------------------------- | -------------- |
| `main`                    | Always releasable; protected                   | Permanent      |
| `feature/<issue>-<slug>`  | One issue, one PR                              | Until PR merge |
| `fix/<issue>-<slug>`      | Bug fix                                        | Until PR merge |
| `security/<issue>-<slug>` | Security fix (may be private until disclosure) | Until PR merge |
| `docs/<issue>-<slug>`     | Documentation only                             | Until PR merge |
| `chore/<issue>-<slug>`    | Config, tooling, dependencies                  | Until PR merge |
| `hotfix/<issue>-<slug>`   | Emergency fix to production (bypasses staging) | Until PR merge |

`main` protection rules: PR required, 1 approval minimum, no force-push, status checks must pass.

---

## Conventional Commits (ADR-0006)

All commits must follow:

```
<type>(<scope>): <subject>

[optional body — explain WHY, not WHAT]

[optional footer — BREAKING CHANGE, Closes #N]
```

### Types

| Type       | When to use                                      | Bumps version |
| ---------- | ------------------------------------------------ | ------------- |
| `feat`     | New capability visible to users or callers       | MINOR         |
| `fix`      | Bug fix in existing functionality                | PATCH         |
| `perf`     | Performance improvement without behaviour change | PATCH         |
| `refactor` | Code restructure without feature or fix          | PATCH         |
| `docs`     | Documentation changes only                       | None          |
| `chore`    | Build config, tooling, dependency updates        | None          |
| `test`     | Adding or fixing tests                           | None          |
| `ci`       | CI/CD pipeline changes                           | None          |
| `security` | Security control or fix                          | PATCH         |
| `revert`   | Reverts a previous commit                        | PATCH         |

### Scopes for this project

`agents` · `guardrails` · `api` · `observability` · `skills` · `specs` · `adr` · `harness` · `infra` · `privacy` · `security`

### Breaking change

Add `BREAKING CHANGE:` footer or `!` after type: `feat!:` or `feat(api)!:`.

---

## Python Coding Standards

### Module structure

```
src/
  domain/
    models/          # Pydantic models — no external imports
    ports/
      inbound/       # abstract base classes for inbound adapters
      outbound/      # abstract base classes for outbound adapters
    services/        # pure domain logic
  application/
    use_cases/       # one file per use case
  adapters/
    inbound/         # REST handlers, Kafka consumers
    outbound/        # LLM, Vault, Prometheus, PagerDuty clients
  guardrails/        # guardrail implementations (treated as domain layer)
  observability/     # structured logging, metrics, tracing setup
  api/               # FastAPI app + routers
```

### Naming conventions

| Entity            | Convention             | Example                |
| ----------------- | ---------------------- | ---------------------- |
| Module / package  | `snake_case`           | `classify_severity.py` |
| Class             | `PascalCase`           | `DetectionAgent`       |
| Function / method | `snake_case`           | `validate_token()`     |
| Constant          | `UPPER_SNAKE_CASE`     | `MIN_CONFIDENCE = 0.6` |
| Pydantic model    | `PascalCase`           | `AgentMessage`         |
| Port interface    | `PascalCase + Port`    | `LLMPort`, `AuditPort` |
| Adapter           | `PascalCase + Adapter` | `AnthropicAdapter`     |
| Test file         | `test_<module>.py`     | `test_hitl_gate.py`    |

### Comments

Write no comments unless the WHY is non-obvious: a hidden constraint, subtle invariant, or workaround for a specific bug. A clear name beats a comment.

### Type hints

All public functions and methods must have complete type hints (enforced by mypy at G12).

```python
def validate_token(token: ApprovalToken, signing_key: bytes) -> None:
    ...
```

### Error handling

- Raise domain exceptions (`HITLValidationError`, `LLMOutputInvalid`, `PiiSanitizationRequired`) defined in `domain/exceptions.py`.
- Never catch and swallow exceptions silently — always write an audit event before re-raising.
- Never use bare `except:` — always catch specific exception types.

### Secrets

No secrets, credentials, or API keys in code or config files (RULE-C03). All secrets accessed via Vault (`vault.get_secret("path/to/secret")`).

---

## Definition of Done (summary — full version in spec 04)

A story is done when:

- [ ] All acceptance criteria from the spec pass
- [ ] Unit coverage ≥ 80% (G01), integration coverage ≥ 60% (G02)
- [ ] Guardrails coverage ≥ 95% branch (G03)
- [ ] Zero Critical/High SAST findings (G04, G05)
- [ ] Zero exposed secrets (G10)
- [ ] Semgrep custom rules clean (G06–G09)
- [ ] Import layer rules respected (G13)
- [ ] PR template filled and CI green
- [ ] CHANGELOG updated automatically by Release Please from Conventional Commit

---

## Code Review Invariants

| Invariant                                         | Check in review                                         |
| ------------------------------------------------- | ------------------------------------------------------- |
| `PRODUCTION_*` only via `action_executor`         | Search for `adapter.execute(` outside `action_executor` |
| `LLMAdapter.complete` with `sanitized=True`       | Semgrep G06 already enforces; spot-check in review      |
| No raw PII in log statements                      | Semgrep G09; check `logger.*` calls near user data      |
| Pydantic validation on every LLM response         | `validate_llm_response()` called before result used     |
| Audit event written before and after every action | `audit.write(...)` present in action path               |
