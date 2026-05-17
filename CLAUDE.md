# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AgenticAI-2-Incident-Response** is a multi-agent AI copilot for IT incident response, designed to reduce MTTD (Mean Time to Detect) and MTTR (Mean Time to Recovery) through AI-orchestrated triage in ~10 seconds. This is a Master's dissertation project (PPGCA / Unisinos) by Valdomiro Souza.

## No Build or Test Commands

This is a pure documentation and skills library repository — Markdown files only. There is no build system, test runner, linter, or CI pipeline to invoke.

## Repository Structure

Two top-level concerns:

1. **Agent Skills (`skills/`)** — 12 reusable agent skills encoding enterprise engineering standards, each following the Anthropic Agent Skills best-practices format.
2. **Root documentation** — `README.md` describes the system; `CLAUDE.md` (this file) guides AI collaboration.

### Skill Layout

Each skill in `skills/<kebab-case-name>/` is self-contained:

```
skills/<skill-name>/
├── SKILL.md           ← mandatory: YAML frontmatter + knowledge body
└── <reference>.md     ← optional: detailed templates or code patterns
```

Single-file skills (content fits in `SKILL.md` alone) are valid — see `ai-governance/`, `cicd-pipeline/`, `documentation-standards/`.

## Skills Library

| Directory                    | Domain                | Key reference files                                                 |
| ---------------------------- | --------------------- | ------------------------------------------------------------------- |
| `sre-foundations/`           | SRE                   | `prr-checklist.md`, `incident-response.md`                          |
| `observability-engineering/` | Observability         | `sli-slo-templates.md`, `instrumentation-guide.md`                  |
| `large-system-design/`       | Architecture          | `nalsd-templates.md`, `resilience-patterns.md`                      |
| `devsecops/`                 | Security/DevOps       | `owasp-controls.md`, `pii-anonymization.md`                         |
| `security-by-design/`        | Security Architecture | `threat-modeling.md`, `privacy-by-design.md`                        |
| `ai-governance/`             | AI Ethics/Governance  | _(SKILL.md only)_                                                   |
| `spec-driven-development/`   | Engineering Process   | `spec-template.md`                                                  |
| `sdlc-governance/`           | SDLC/Governance       | `rfc-template.md`, `tech-debt-process.md`, `deprecation-process.md` |
| `managing-adrs/`             | Architecture Docs     | `adr-template.md`, `adr-examples.md`                                |
| `credentials-and-secrets/`   | Security/Infra        | `least-privilege.md`, `gitignore-template.md`                       |
| `cicd-pipeline/`             | DevOps                | _(SKILL.md only)_                                                   |
| `documentation-standards/`   | Documentation         | _(SKILL.md only)_                                                   |

## Authoring Standards for Skills

### SKILL.md Frontmatter (mandatory)

Every `SKILL.md` must open with YAML frontmatter containing exactly `name` and `description`:

```yaml
---
name: <kebab-case-matching-directory-name>
description: <trigger clause — see format below>
---
```

### Description / Trigger Clause Format

The `description` field is how agent runtimes decide when to load the skill. Pattern used across all existing skills:

> _[What the skill does — one sentence]. Use when [primary conditions]. Also use when [someone asks about X, Y, Z keywords]._

Example from `sre-foundations`:

> "Applies Google SRE principles to production systems — Production Readiness Reviews, TOIL reduction, incident lifecycle, and blameless postmortems. Use when preparing a service for production, evaluating operational maturity, responding to incidents, or writing postmortems. Also use when someone asks about on-call, error budgets, SRE engagement, or reducing manual operational work."

Keep it keyword-rich: include both the formal term and common synonyms an agent might receive.

### SKILL.md Body Convention

Existing skills follow a consistent opening structure:

1. `## Core principle` — one-paragraph philosophy statement
2. `## Contents` — bulleted index with relative links to reference files

### Reference Files

- Linked from `SKILL.md` using relative Markdown links: `[filename.md](filename.md)`
- Contain the heavy content: templates, code examples, checklists
- Use a reference file when content would make `SKILL.md` hard to scan; stay single-file when the full content is concise

### Naming Conventions

- Directory names: `kebab-case` (always lowercase, hyphens as separators)
- Skill entry point: `SKILL.md` (always uppercase)
- Reference files: `lowercase-kebab.md`

## Adding a New Skill — Workflow

1. Create `skills/<new-skill-name>/` directory
2. Write `SKILL.md` with frontmatter (`name`, `description`) and body (`Core principle`, `Contents`)
3. Extract heavy content (templates, code) into named reference files in the same directory
4. Link reference files from `SKILL.md` using relative links
5. Add a row to the Skills Library table in this file and in `skills/README.md`
6. Add the traceability header (see AI Governance Rules below) if AI-generated

## Compliance Frameworks Applied

Skills are aligned with: Google SRE Book, OWASP Top 10 + ASVS, LGPD (Lei 13.709) + GDPR, EU AI Act, OpenTelemetry, SLSA, ISO/IEC 27001, PCI-DSS, NIST CSF.

## AI Governance Rules

- AI outputs are suggestions only — a human engineer must review, test, and approve before use in production.
- PII must not be sent to external AI models without a DPA and prior anonymization.
- Prompts are versioned under `prompts/v<N>/` and follow the same PR review process as code.
- All AI usage in critical flows must be logged and traceable.

Every AI-generated file must include this traceability header:

```
# ============================================================
# AI-GENERATED ARTIFACT
# Generated by  : Claude Sonnet 4.6 / [model]
# Prompt ID     : [hash or traceable ID]
# Generated at  : [ISO-8601 timestamp]
# Reviewed by   : [engineer name]
# Approved at   : [ISO-8601 timestamp]
# Spec reference: [SPEC-ID]
# ============================================================
```

AI risk classification for this project's incident-response flows falls under **Medium Risk** (AI analyzing production logs, AI in incident response flows) — Tech Lead + SecOps review required.
