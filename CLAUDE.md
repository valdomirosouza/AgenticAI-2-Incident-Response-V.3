# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AgenticAI-2-Incident-Response** is a multi-agent AI copilot for IT incident response, designed to reduce MTTD (Mean Time to Detect) and MTTR (Mean Time to Recovery) through AI-orchestrated triage in ~10 seconds. This is a Master's dissertation project (PPGCA / Unisinos) by Valdomiro Souza.

## Repository Structure

This repository contains two top-level concerns:

1. **Agent Skills (`skills/`)** — A library of 12 reusable agent skills encoding enterprise engineering standards. Each skill follows the Anthropic Agent Skills best practices format with a `SKILL.md` (frontmatter + content) and optional reference files.

2. **Root documentation** — `README.md` describes the system; `CLAUDE.md` (this file) guides AI collaboration.

### Skills Architecture

Each skill in `skills/<skill-name>/` is self-contained:

- `SKILL.md` — frontmatter (`name`, `description`) + knowledge content
- Reference files (e.g., `prr-checklist.md`, `threat-modeling.md`) — detailed templates and code patterns linked from `SKILL.md`

The `description` frontmatter field is the trigger clause used by agent runtimes to decide when to apply the skill — keep it precise and keyword-rich.

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

When creating or editing skills:

- **Frontmatter is mandatory** — every `SKILL.md` must have `name` and `description` fields in YAML frontmatter.
- **Description field = trigger clause** — write it as "Use when: [specific conditions]" covering keywords an agent runtime will match against.
- **Reference files use relative links** — link from `SKILL.md` to sibling files using `[filename.md](filename.md)`.
- **Single-file skills** are valid when content is concise (see `ai-governance/`, `cicd-pipeline/`, `documentation-standards/`).
- **AI traceability** — AI-generated artifacts must include the traceability header defined in `ai-governance/SKILL.md` (model, prompt ID, reviewer, approval timestamp, spec reference).

## Compliance Frameworks Applied

Skills are aligned with: Google SRE Book, OWASP Top 10 + ASVS, LGPD (Lei 13.709) + GDPR, EU AI Act, OpenTelemetry, SLSA, ISO/IEC 27001, PCI-DSS, NIST CSF.

## AI Governance Rules (from `ai-governance/SKILL.md`)

- AI outputs are suggestions only — a human engineer must review, test, and approve before use in production.
- PII must not be sent to external AI models without a DPA and prior anonymization.
- Prompts are versioned in the repository under `prompts/v<N>/` and follow the same PR review process as code.
- All AI usage in critical flows must be logged and traceable.
