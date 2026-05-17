# Project Skills Catalog — Agentic AI Incident Response Copilot

> Extracted from CLAUDE.md §4.1. Describes the planned project-specific skill files under `skills/`.
> For the skill activation routing table (what to load per context), see CLAUDE.md §4.1.
> For enterprise-grade shared skills already available, see `skills/README.md`.

> **Language rule**: All skills, their content, checklists, templates, and generated
> artifacts are written in **English**. No exceptions. Language-specific compliance
> references (LGPD, GDPR) use their official English terminology.

```
skills/
│
├── writing/                               ← Technical writing (all skills in English)
│   ├── tech-docs.md                         · Technical documentation for implementations
│   │                                          · Component and service READMEs
│   │                                          · Installation and configuration guides
│   │                                          · API reference (endpoints, parameters, examples)
│   │                                          · Operational runbooks and playbooks
│   │                                          · Architecture diagrams: C4, sequence, flowchart
│   └── release-notes.md                     · Changelogs and release notes
│                                              · Keep a Changelog + SemVer
│                                              · Sections: Added | Changed | Fixed |
│                                                           Deprecated | Removed | Security
│                                              · Traceability: issue/ADR reference per entry
│
├── sdlc/                                  ← Software Development Lifecycle
│   ├── requirements.md                      · User stories, acceptance criteria, Definition of Done
│   │                                          · Format: "As [role], I want [action], so that [value]"
│   │                                          · INVEST criteria (Independent, Negotiable,
│   │                                            Valuable, Estimable, Small, Testable)
│   ├── design.md                            · System design and architecture review
│   │                                          · Design Review (DR) checklist
│   │                                          · Patterns: Clean Architecture, Hexagonal, CQRS
│   │                                          · Documentation: C4 Model (Context, Container,
│   │                                            Component, Code)
│   ├── implementation.md                    · Secure code patterns and review
│   │                                          · Conventional Commits (feat, fix, chore,
│   │                                            docs, refactor, test, ci, security)
│   │                                          · Branch strategy: trunk-based / GitFlow
│   │                                          · Naming: feature/, fix/, hotfix/, chore/,
│   │                                            release/ with mandatory ticket-id
│   ├── pull-request.md                      · Full PR and Code Review flow
│   │
│   │                                          ── PR OPENING ──
│   │                                          · Mandatory PR template:
│   │                                            · Description: what and why (not how)
│   │                                            · Linked issue/ticket (Closes #N)
│   │                                            · Related ADR (if architectural decision)
│   │                                            · Type: feat | fix | hotfix | refactor |
│   │                                              security | docs | chore
│   │                                            · Author checklist before opening:
│   │                                              ☐ Tests written and passing locally
│   │                                              ☐ Harness run without failures
│   │                                              ☐ SAST executed (no Critical/High)
│   │                                              ☐ PII/secrets verified (no exposure)
│   │                                              ☐ Documentation updated if needed
│   │                                              ☐ CHANGELOG.md updated
│   │                                              ☐ Self-review completed (full diff)
│   │
│   │                                          ── AUTOMATED GATES (CI) ──
│   │                                          · All gates must be GREEN to enable
│   │                                            merge — no exceptions:
│   │                                            · Build: compile with no errors or warnings
│   │                                            · Unit tests: coverage ≥ 80%
│   │                                            · Integration tests: coverage ≥ 60%
│   │                                            · SAST: zero Critical or High findings
│   │                                            · Secrets scan: zero exposed secrets
│   │                                              (git-secrets, truffleHog, gitleaks)
│   │                                            · Dependency scan: zero Critical CVEs
│   │                                            · Lint: zero errors (warnings allowed)
│   │                                            · License check: no restrictive licenses
│   │                                              (GPL, AGPL) without approved ADR
│   │
│   │                                          ── CODE REVIEW (HUMAN REVIEW) ──
│   │                                          · Minimum approvals by PR type:
│   │                                            · feat / fix: 1 approval
│   │                                            · refactor / chore: 1 approval
│   │                                            · security / hotfix: 2 approvals
│   │                                            · change to skill, rule or ADR: 2 approvals
│   │                                            · CI/CD pipeline change: 2 approvals
│   │
│   │                                          · Reviewer checklist (analysis dimensions):
│   │
│   │                                            [Correctness and Logic]
│   │                                            ☐ Is the logic correct for all cases?
│   │                                            ☐ Edge cases and failures handled explicitly?
│   │                                            ☐ No race conditions or hidden side effects?
│   │
│   │                                            [Security]
│   │                                            ☐ No input without validation/sanitization?
│   │                                            ☐ No hardcoded secrets, tokens or passwords?
│   │                                            ☐ PII handled per privacy/pii.md?
│   │                                            ☐ No SQL injection, XSS, SSRF or path traversal?
│   │                                            ☐ OWASP LLM checklist applied (if Agentic AI)?
│   │
│   │                                            [Quality and Maintainability]
│   │                                            ☐ Functions with single responsibility (SRP)?
│   │                                            ☐ Expressive names — no obscure abbreviations?
│   │                                            ☐ No dead code, loose TODOs or print statements?
│   │                                            ☐ Cyclomatic complexity acceptable (≤ 10)?
│   │                                            ☐ Duplication eliminated (DRY)?
│   │
│   │                                            [Tests]
│   │                                            ☐ Tests cover behavior, not implementation?
│   │                                            ☐ Failure and exception cases tested?
│   │                                            ☐ Fixtures use real corpus data (no mock)?
│   │
│   │                                            [Observability]
│   │                                            ☐ Structured logs at critical points?
│   │                                            ☐ Metrics instrumented (Golden Signals)?
│   │                                            ☐ trace_id propagated correctly?
│   │                                            ☐ No PII exposed in logs or traces?
│   │
│   │                                            [Documentation]
│   │                                            ☐ Docstring/comment where logic is not
│   │                                              self-explanatory?
│   │                                            ☐ README or tech-doc updated?
│   │                                            ☐ ADR created if architectural decision?
│   │
│   │                                          ── FEEDBACK RESOLUTION ──
│   │                                          · Every comment must be answered or
│   │                                            resolved before requesting re-review
│   │                                          · "Request Changes" requires new CI run
│   │                                            before new approval
│   │                                          · Design discussions unresolved in
│   │                                            2 days → escalate to tech lead
│   │
│   │                                          ── MERGE ──
│   │                                          · Default strategy: Squash and Merge
│   │                                            (clean history on main)
│   │                                          · Exception: Merge Commit for releases and
│   │                                            hotfixes (version traceability)
│   │                                          · Branch deleted after merge (mandatory)
│   │                                          · Version tag created automatically
│   │                                            by pipeline if release/ branch
│   ├── testing.md                           · Test strategy by layer
│   │                                          · Pyramid: Unit → Integration → E2E → Contract
│   │                                          · Minimum coverage: 80% unit, 60% integration
│   │                                          · Mutation testing and property-based testing
│   ├── deployment.md                        · Safe deployment strategies
│   │                                          · Blue-Green, Canary, Feature Flags
│   │                                          · Automatic rollback on SLO breach
│   │                                          · Gates: smoke test → health check → promote
│   └── operations.md                        · Post-deploy and continuous operations
│                                              · Runbook per service (mandatory)
│                                              · Post-mortem template (blameless)
│                                              · SLO/SLA/SLI: definition and periodic review
│
├── observability/                         ← Observability: Logs, Metrics and Traces
│   ├── logs.md                              · Structured logging (JSON)
│   │                                          · Levels: DEBUG | INFO | WARN | ERROR | FATAL
│   │                                          · Mandatory fields: timestamp, service,
│   │                                            trace_id, span_id, level, message, user_id
│   │                                          · Correlation with traces via trace_id
│   │                                          · Retention and PII masking
│   ├── metrics.md                           · Golden Signals (Google SRE Book)
│   │                                          · Latency: p50, p95, p99 (not just average)
│   │                                          · Error Rate: % of requests with 5xx/4xx error
│   │                                          · Traffic: req/s, events/s per service
│   │                                          · Saturation: CPU%, memory%, queue, threads
│   │                                          · Instrumentation: Prometheus / OpenMetrics
│   │                                          · Alerts: thresholds by SLO, not fixed value
│   ├── traces.md                            · Distributed tracing (OpenTelemetry)
│   │                                          · Mandatory span per critical operation
│   │                                          · Context propagation: W3C TraceContext
│   │                                          · Sampling: head-based vs tail-based
│   │                                          · IR integration: traces as primary source
│   │                                            for Root Cause Analysis (RCA)
│   └── dashboards.md                        · Dashboard standard by audience
│                                              · Level 1 — NOC/On-call: Golden Signals real-time
│                                              · Level 2 — Engineering: breakdown by service/endpoint
│                                              · Level 3 — Business: CUJ (Critical User Journey)
│                                              · USE Method (Utilization, Saturation, Errors)
│                                                for infrastructure resources
│
├── devsecops/                             ← Security integrated into the development cycle
│   ├── secure-development.md               · Secure development by SDLC phase
│   │                                          · Threat Modeling (STRIDE) in design phase
│   │                                          · Principles: least privilege, defense-in-depth,
│   │                                            fail-safe defaults, zero trust
│   │                                          · Secrets management: never hardcode; use vault
│   │                                          · Dependency pinning + SCA
│   ├── owasp.md                             · OWASP Top 10 (Web) and LLM Top 10 (AI/Agents)
│   │                                          · Checklist per risk category
│   │                                          · OWASP LLM relevant for Agentic AI:
│   │                                            · LLM01 Prompt Injection
│   │                                            · LLM02 Insecure Output Handling
│   │                                            · LLM06 Sensitive Information Disclosure
│   │                                            · LLM08 Excessive Agency
│   │                                            · LLM09 Overreliance
│   │                                          · Mitigations per item with ADR reference
│   ├── sast.md                              · Static Application Security Testing
│   │                                          · Tools: Semgrep, Bandit (Python),
│   │                                            CodeQL, SonarQube
│   │                                          · Mandatory gate on PR/MR: blocks merge
│   │                                            on Critical or High findings
│   │                                          · Custom rules for project patterns
│   │                                          · CI/CD pipeline integration
│   ├── dast.md                              · Dynamic Application Security Testing
│   │                                          · Tools: OWASP ZAP, Burp Suite (CI mode)
│   │                                          · Execution: post-deploy in staging environment
│   │                                          · Scope: public endpoints + internal APIs
│   │                                          · Mandatory report before release
│   └── supply-chain.md                      · Supply chain security (SLSA)
│                                              · SBOM generated per build (CycloneDX or SPDX)
│                                              · Dependency pinning + hash verification
│                                              · License verification (GPL, AGPL: alert)
│                                              · CVE scanning: Trivy, Grype, Snyk
│
├── ethics/                                ← AI ethics and autonomous systems
│   ├── ai-ethics.md                         · Ethical and responsible AI principles
│   │                                          · Fairness: algorithmic bias detection
│   │                                            and mitigation (AEQUITAS, Fairlearn)
│   │                                          · Accountability: agent decision traceability
│   │                                            — who decided, when and why
│   │                                          · Transparency: explainability (XAI) of
│   │                                            recommendations and autonomous actions
│   │                                          · Non-maleficence: negative impact analysis
│   │                                            before enabling autonomy in production
│   │                                          · Reference frameworks: EU AI Act,
│   │                                            NIST AI RMF, IEEE Ethically Aligned Design
│   ├── agentic-ethics.md                    · Ethics specific to Agentic AI systems
│   │                                          · Autonomy levels and proportional risks
│   │                                          · Consent and user communication
│   │                                            about autonomously executed actions
│   │                                          · Delegation limits: what the agent NEVER
│   │                                            can do without explicit human approval
│   │                                          · Shadow agents: detection and prevention of
│   │                                            unintentional emergent behavior
│   │                                          · Value alignment and reward hacking prevention
│   └── bias-fairness.md                     · Bias in observability data and IR
│                                              · Survivorship bias in incident datasets
│                                              · Fairness across monitored teams/services
│                                              · Periodic audit of agent decisions
│                                                by service group or criticality
│
├── privacy/                               ← Personal data protection and privacy
│   ├── pii.md                               · PII identification and classification
│   │                                          · Personal data categories:
│   │                                            · Direct: name, CPF, email, phone,
│   │                                              IP address, device ID, user_id
│   │                                            · Sensitive: health, racial origin, biometrics,
│   │                                              religion, political opinion (LGPD art. 11)
│   │                                            · Inferred: behavior, location,
│   │                                              usage patterns, incident profile
│   │                                          · PII in logs and traces: mandatory masking
│   │                                            before ingestion into observability
│   │                                          · PII in LLM prompts: sanitization and
│   │                                            pseudonymization before sending to API
│   │                                          · Data inventory: PII flow map
│   │                                            per service (Data Flow Diagram — DFD)
│   ├── lgpd.md                              · Lei Geral de Proteção de Dados (Lei 13.709/2018)
│   │                                          · Legal bases for processing (art. 7 and 11)
│   │                                          · Data subject rights: access, correction,
│   │                                            deletion, portability, revocation
│   │                                          · DPO role and obligations
│   │                                          · Data Protection Impact Report
│   │                                            (RIPD) for systems with autonomous AI
│   │                                          · Security incidents: ANPD notification
│   │                                            within 72h (art. 48)
│   │                                          · International data transfer:
│   │                                            restrictions and required safeguards
│   ├── gdpr.md                              · General Data Protection Regulation (EU 2016/679)
│   │                                          · Principles: lawfulness, fairness, transparency,
│   │                                            purpose limitation, data minimisation,
│   │                                            accuracy, storage limitation, integrity
│   │                                          · Legal bases: consent, contract, legal
│   │                                            obligation, vital interests, public task,
│   │                                            legitimate interests
│   │                                          · Data Subject Rights: access, erasure
│   │                                            (right to be forgotten), portability,
│   │                                            restriction, objection, no profiling
│   │                                          · DPIA mandatory for high-risk AI
│   │                                          · Breach notification: 72h to supervisory
│   │                                            authority + communication to data subjects
│   │                                          · Cross-border transfers: Standard Contractual
│   │                                            Clauses (SCCs), Binding Corporate Rules
│   ├── data-protection.md                   · General data protection best practices
│   │                                          · Privacy by Design (PbD) — 7 principles
│   │                                            by Ann Cavoukian integrated into SDLC
│   │                                          · Privacy by Default: most restrictive
│   │                                            configuration as the default
│   │                                          · Data retention: explicit policy with
│   │                                            TTL (Time to Live) per category
│   │                                          · Encryption: in transit (TLS 1.3) and
│   │                                            at rest (AES-256); keys rotated
│   │                                          · Role-based access control (RBAC)
│   │                                            and need-to-know principle
│   │                                          · Secure backup: encrypted, tested,
│   │                                            with retention aligned to data policy
│   └── anonymization.md                     · Anonymization and pseudonymization techniques
│                                              · Legal distinction: anonymized data (outside
│                                                LGPD/GDPR) vs pseudonymized (still PII)
│                                              · Anonymization techniques:
│                                                · k-Anonymity: indistinguishability guarantee
│                                                  among k records for quasi-identifiers
│                                                · l-Diversity: diversity in sensitive attributes
│                                                  within each group
│                                                · t-Closeness: sensitive attribute distribution
│                                                  close to global distribution
│                                                · Differential Privacy (DP): noise calibrated
│                                                  by ε (epsilon) for datasets and models
│                                              · Pseudonymization techniques:
│                                                · Tokenization: reversible token replacement
│                                                  with secure key
│                                                · Hashing with salt: SHA-256 + unique salt
│                                                  per tenant (irreversible without salt)
│                                                · Masking: partial replacement for logs
│                                                  (e.g. "user@***.com", "***-456")
│                                              · Anonymization in observability pipelines:
│                                                mandatory before sending to LLMs and
│                                                third-party analysis systems
│                                              · Validation: re-identification risk assessment
│                                                after anonymization (Singling Out,
│                                                Linkability, Inference tests)
│
├── engineering/                           ← Project engineering
│   ├── adr-template.md                      · Canonical ADR template (see docs/adr/README.md)
│   ├── spec-template.md                     · SDD template for research and system specs
│   └── harness-config.md                    · Harness check configuration
│
└── domain/                                ← Domain: Agentic AI + Incident Response
    ├── agentic-ai-taxonomy.md               · AI Agent vs Agentic AI vs Copilot
    ├── incident-lifecycle.md                · Failure Perception → RCA → Remediation
    ├── mttd-mttr-metrics.md                 · Definitions, formulas, market benchmarks
    └── guardrails-patterns.md               · HITL, HOTL, kill-switch, rollback patterns
```

---

_Source: CLAUDE.md §4.1 | Skill activation routing table: CLAUDE.md §4.1 | Enterprise shared skills: `skills/README.md`_
