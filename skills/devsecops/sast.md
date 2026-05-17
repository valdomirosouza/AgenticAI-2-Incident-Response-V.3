# Skill: SAST

**Domain**: devsecops
**Activation triggers**: SAST, static analysis, Semgrep, Bandit, CodeQL, SonarQube, static security testing, code scanning, custom rules, security finding, false positive
**References**: specs/security/13-sast-dast-policy.md, ADR-0017, ADR-0018

---

## SAST Toolchain (spec 13)

Four tools run on every PR as CI gates G04 and G05. All must be clean before merge.

| Tool    | Scope                                  | Gate    | Finding threshold  |
| ------- | -------------------------------------- | ------- | ------------------ |
| Semgrep | Python source + custom rules (4 rules) | G04/G05 | Zero Critical/High |
| Bandit  | Python security anti-patterns          | G04/G05 | Zero Critical/High |
| CodeQL  | Semantic analysis — injection, auth    | G04     | Zero Critical      |
| Checkov | Terraform / Helm / Docker misconfig    | G04/G05 | Zero Critical/High |

---

## Four Custom Semgrep Rules (ADR-0017)

These project-specific rules enforce architectural invariants that generic tools cannot detect.

### Rule 1: `llm-unsanitized-prompt` (Gate G06)

Detects: `LLMAdapter.complete()` called without `sanitized=True`.

```yaml
# .semgrep/llm-unsanitized-prompt.yml
rules:
  - id: llm-unsanitized-prompt
    patterns:
      - pattern: $ADAPTER.complete($PROMPT)
      - pattern-not: $ADAPTER.complete($PROMPT, sanitized=True)
    message: >
      LLMAdapter.complete() called without sanitized=True.
      Call pii_sanitizer.sanitize(prompt) first, then pass sanitized=True.
    languages: [python]
    severity: ERROR
    fix: "$ADAPTER.complete($PROMPT, sanitized=True)"
```

### Rule 2: `hitl-bypass` (Gate G07)

Detects: direct call to `adapter.execute()` outside `action_executor`.

```yaml
# .semgrep/hitl-bypass.yml
rules:
  - id: hitl-bypass
    patterns:
      - pattern: $ADAPTER.execute(...)
      - pattern-not-inside: |
          def execute(...):
            ...
    paths:
      exclude:
        - src/adapters/outbound/action_executor.py
    message: >
      Direct adapter.execute() call detected outside action_executor.
      All PRODUCTION_* actions must go through action_executor.execute(action, token=...).
    languages: [python]
    severity: ERROR
```

### Rule 3: `secret-in-env` (Gate G08)

Detects: hard-coded credential patterns in Python or config files.

```yaml
# .semgrep/secret-in-env.yml
rules:
  - id: secret-in-env
    pattern-either:
      - pattern: $KEY = "sk-..."
      - pattern: $KEY = "anthropic-..."
      - pattern: os.environ["ANTHROPIC_API_KEY"] = "..."
      - pattern: api_key = "..."
    message: Hard-coded credential detected. Use vault.get_secret() instead.
    languages: [python]
    severity: ERROR
```

### Rule 4: `raw-log-pii` (Gate G09)

Detects: logger call with raw user input (no prior masking call).

```yaml
# .semgrep/raw-log-pii.yml
rules:
  - id: raw-log-pii
    patterns:
      - pattern: logger.$LEVEL($MSG, ...)
      - pattern-not-inside: |
          $X = pii_sanitizer.sanitize(...)
          ...
          logger.$LEVEL(...)
    focus-metavariable: $MSG
    pattern-regex: ".*user.*|.*email.*|.*ip.*|.*request.*body.*"
    message: Potential PII in log call. Call pii_sanitizer.sanitize() before logging.
    languages: [python]
    severity: WARNING
```

---

## Remediation SLAs (spec 13)

| Severity | SLA to remediate or accept-risk | Can ship to production while open? |
| -------- | ------------------------------- | ---------------------------------- |
| Critical | 24 hours                        | **No** — blocks release gate       |
| High     | 5 business days                 | **No** — blocks PR merge (G05)     |
| Medium   | 30 calendar days                | Yes — tracked in security backlog  |
| Low      | 90 calendar days                | Yes — tracked in security backlog  |
| Info     | No SLA                          | Yes                                |

Critical findings have **no accept-risk path** — must be fixed.

---

## False Positive Process (spec 13)

1. Engineer flags finding as FP in PR comment with written justification.
2. Security Lead reviews within **2 business days**.
3. If accepted: finding suppressed in `.semgrep-ignore` with 90-day expiry date and reason.
4. If rejected: engineer must fix before merge.
5. All FP decisions logged in `docs/security/false-positives.md` (date, finding ID, justification, approver).

**Prohibition:** `# nosemgrep` inline suppressions are forbidden except in `tests/fixtures/`. Circumventing a rule without Security Lead approval is a policy violation.

---

## Running SAST Locally

```shell
# Semgrep — all rules including custom
semgrep --config .semgrep/ --config p/python --config p/secrets src/

# Bandit
bandit -r src/ -ll  # -ll = only Medium and above

# CodeQL (requires GitHub CLI + CodeQL CLI)
codeql database create codeql-db --language=python --source-root src/
codeql analyze codeql-db python-security-and-quality.qls

# Checkov — IaC
checkov -d infrastructure/ --framework terraform,helm,dockerfile
```

---

## Adding a New Custom Rule

1. Write the rule in `.semgrep/<rule-id>.yml` following the patterns above.
2. Add a test fixture in `tests/security/semgrep/<rule-id>/` with:
   - `bad.py` — code that should trigger the rule
   - `good.py` — code that should not trigger the rule
3. Run `semgrep --test tests/security/semgrep/<rule-id>/` to verify.
4. Add the rule ID to the relevant gate column in `harness/code-check.yml`.
5. PR requires Security Lead review.
