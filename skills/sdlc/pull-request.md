# Skill: Pull Request

**Domain**: sdlc
**Activation triggers**: Pull request, PR, code review, merge, PR checklist, CI gate, reviewer, approval, merge strategy, PR template
**References**: specs/sdlc/06-pr-and-review-process.md, ADR-0007, CLAUDE.md §8 step 8

---

## PR Lifecycle

```
feature/* branch
      │
      ▼ git push + gh pr create
      │
      ▼ CI runs all gates (G01–G14 + D01–D04 if docs changed)
      │
      ▼ Reviewer assigned (see §Reviewer Assignment)
      │
      ▼ Author resolves all comments
      │
      ▼ Minimum approvals met + all CI green
      │
      ▼ Squash-merge into main → branch deleted
      │
      ▼ Release Please PR updated automatically
```

---

## Author Checklist (fill before requesting review)

### Code changes

- [ ] Branch name follows convention: `<type>/<issue>-<slug>` (ADR-0005)
- [ ] Commit messages follow Conventional Commits format (ADR-0006)
- [ ] PR title matches commit type: `feat(scope): subject` or `fix(scope): subject`
- [ ] All acceptance criteria from the linked spec pass
- [ ] Unit coverage ≥ 80% — run `pytest --cov=src tests/unit/` locally
- [ ] Integration coverage ≥ 60% — run `pytest --cov=src tests/integration/` locally
- [ ] Guardrails coverage ≥ 95% branch — run `pytest --cov=src/guardrails tests/unit/guardrails/` locally
- [ ] `mypy src/` clean (zero errors)
- [ ] `semgrep --config .semgrep/ src/` clean (zero findings including custom rules)
- [ ] `gitleaks detect` clean (zero secrets)
- [ ] Import layer rules respected (hexagonal architecture AC-01–AC-06)
- [ ] No PII in test fixtures — use role labels or synthetic data (RULE-C02)
- [ ] No secrets or credentials in any committed file (RULE-C03)

### Documentation changes (if docs/specs/skills modified)

- [ ] Spec has all 5 mandatory sections (D01)
- [ ] ADR has `**Status**:` field (D02)
- [ ] No real PII in documentation (D03)
- [ ] No secrets or real hostnames in documentation (D04)
- [ ] Language: English only (RULE-005)

### PR description

- [ ] Issue linked: `Closes #N`
- [ ] Spec referenced by file path
- [ ] ADRs listed (if new or updated)
- [ ] Test plan checklist included

---

## PR Description Template

```markdown
## Summary

- One-line bullet per significant change

## Spec

Derived from `specs/<domain>/<NN>-<name>.md`

## ADRs

- New ADR: `docs/adr/ADR-NNNN-<name>.md` (if applicable)
- Implements: ADR-XXXX, ADR-YYYY

## Test plan

- [ ] Unit tests added for all new paths in `tests/unit/`
- [ ] Integration tests added in `tests/integration/`
- [ ] Guardrail failure paths tested (each guardrail has a negative test)
- [ ] No PII in fixtures

Closes #N
```

---

## Reviewer Assignment

| PR type                                     | Required reviewers                                  | Minimum approvals |
| ------------------------------------------- | --------------------------------------------------- | ----------------- |
| Feature (`feat:`)                           | 1 engineer (domain knowledge)                       | 1                 |
| Security (`security:` or `specs/security/`) | Security Lead + Tech Lead                           | 2                 |
| Privacy (`specs/privacy/` or PII change)    | DPO + Legal                                         | 2                 |
| Ethics (`specs/ethics/` or autonomy change) | Tech Lead + Ethics reviewer                         | 2                 |
| ADR (new or superseded)                     | Domain expert for the ADR's domain                  | 1                 |
| Release (`chore(main): release`)            | Release Please automated — no human reviewer needed | 0 (auto-merge)    |

---

## CI Gates Summary (all must be green before merge)

### Code gates (always run on PR)

| Gate | Check                               | Tool                      |
| ---- | ----------------------------------- | ------------------------- |
| G01  | Unit coverage ≥ 80%                 | pytest-cov                |
| G02  | Integration coverage ≥ 60%          | pytest-cov                |
| G03  | Guardrails coverage ≥ 95% branch    | pytest-cov                |
| G04  | Zero Critical SAST                  | Semgrep + Bandit + CodeQL |
| G05  | Zero High SAST                      | Semgrep + Bandit          |
| G06  | `llm-unsanitized-prompt` rule clean | Semgrep                   |
| G07  | `hitl-bypass` rule clean            | Semgrep                   |
| G08  | `secret-in-env` rule clean          | Semgrep                   |
| G09  | `raw-log-pii` rule clean            | Semgrep                   |
| G10  | Zero exposed secrets                | Gitleaks                  |
| G11  | Zero Critical CVEs                  | pip-audit                 |
| G12  | mypy clean                          | mypy + pydantic           |
| G13  | Import layer rules                  | import-linter             |
| G14  | Conventional Commit format          | commitlint                |

### Doc gates (run when docs/specs/skills modified)

| Gate | Check                     | Tool          |
| ---- | ------------------------- | ------------- |
| D01  | Spec 5 mandatory sections | mdlint custom |
| D02  | ADR Status field present  | grep          |
| D03  | No PII in docs            | Presidio scan |
| D04  | No secrets in docs        | Gitleaks      |

---

## Merge Rules

- **Strategy**: squash-merge only — one clean commit per PR on `main`
- **Branch deletion**: always delete source branch after merge
- **No merge commits**: rebase if the branch is behind `main` before merge
- **Never force-push `main`**: protected branch; even admins should not
- **Release Please PRs**: merged with `--squash --admin` (solo project bypass)

---

## Handling Review Feedback

1. Address every comment — either fix it or explain why it should not be changed.
2. Mark comments as resolved only after the fix is pushed.
3. Re-request review after all comments are addressed.
4. Do not resolve reviewer's comments yourself — the reviewer resolves them.
5. For disagreements: discuss in the comment thread; escalate to Tech Lead if unresolved after two exchanges.
