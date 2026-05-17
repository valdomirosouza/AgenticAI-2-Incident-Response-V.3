# ADR-0001: Adoption of C4 Model for Architecture Documentation

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Researcher)
**Affected RQs**: RQ1 (system architecture), RQ2 (observability pipeline)

---

## Context

The Agentic AI Incident Response Copilot is a distributed, multi-agent system with
multiple integration surfaces (observability backends, LLM APIs, runbook stores,
human approval interfaces). Documenting its architecture for a Master's dissertation
requires a notation that:

1. Is hierarchical — stakeholders at different levels (researcher, examiner, future developer)
   need different levels of detail without maintaining separate, out-of-sync diagrams.
2. Is tooling-agnostic — the project must not depend on proprietary diagramming tools
   to remain reproducible and open.
3. Is widely understood in industry and academia — the notation must be intelligible
   without a legend for qualified reviewers (SRE leads, examiners, AI engineers).
4. Supports traceability — every component in the diagram must map to a spec file
   in `specs/` and a source directory in `src/`.
5. Complies with ISO 27001 A.12.1 (documented operating procedures) — architecture
   documentation must be maintained and version-controlled alongside the code.

Alternatives were evaluated against these five criteria.

## Decision

We adopt the **C4 Model** (Simon Brown, c4model.com) as the standard for all architecture
documentation in this project.

The four levels used:

| Level        | Audience                    | Tool / Format         | Stored in            |
| ------------ | --------------------------- | --------------------- | -------------------- |
| L1 Context   | Examiners, stakeholders     | Mermaid `C4Context`   | `docs/architecture/` |
| L2 Container | Tech Lead, SRE              | Mermaid `C4Container` | `docs/architecture/` |
| L3 Component | Developers                  | Mermaid `C4Component` | `docs/architecture/` |
| L4 Code      | Developers (on demand only) | Generated from code   | Inline in specs      |

All diagrams are authored in **Mermaid** (C4 extension) so they render natively in
GitHub Markdown and require no external tooling. L4 diagrams are generated on demand
from code, not maintained manually, to avoid documentation drift.

Every diagram file is versioned alongside the code it describes. Diagram updates are
required whenever a component boundary changes (ADR supersedes or spec changes).

## Alternatives Considered

| Alternative                   | Pros                                                                                | Cons                                                                            |
| ----------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **UML (class/sequence)**      | Widely known, rich semantic precision                                               | No system-level overview; no standard tool-agnostic text format; verbose        |
| **ArchiMate**                 | Enterprise-grade, supports governance layers                                        | High learning curve; requires licensed tooling (Archi); overkill for research   |
| **Informal boxes-and-arrows** | Zero learning curve, fast to sketch                                                 | Not reproducible; no level hierarchy; fails ISO 27001 documentation requirement |
| **arc42**                     | Covers full architecture documentation lifecycle                                    | Document template, not a diagram notation; does not address the notation gap    |
| **C4 Model** ✅               | Hierarchical, tool-agnostic, text-as-code (Mermaid), widely adopted in cloud-native | L4 can drift if maintained manually — mitigated by generating L4 from code      |

## Consequences

**Positive:**

- Single notation for all levels: researchers, examiners and developers read the same
  diagrams at the appropriate zoom.
- Mermaid renders in GitHub PRs and issues without plugins — zero tooling friction.
- Traceability from L2 Container to `specs/` files and `src/` directories is explicit
  and enforceable in the doc harness (`harness/doc-check.yml`).
- Satisfies ISO 27001 A.12.1: architecture documentation is version-controlled,
  reviewed on change, and co-located with the system it describes.
- Supports EU AI Act Art. 13 (transparency): system boundaries and component interactions
  are documented and auditable.

**Negative / Trade-offs:**

- Mermaid C4 extension has limited layout control — complex diagrams may require manual
  arrangement or splitting into sub-diagrams.
- L3 Component diagrams require discipline to keep in sync with code; enforced via
  doc-gate harness check on changes to `src/`.
- Team members unfamiliar with C4 need a brief onboarding (mitigated by this ADR and
  the `docs/architecture/README.md` guide to be authored in issue #9).

## Review Criteria

Revisit this decision if:

- The Mermaid C4 extension is deprecated or stops rendering in GitHub.
- The dissertation examiner board requires a specific notation (e.g. UML) as a
  formal requirement — in which case a supplementary notation ADR is created.
- A collaborator joins who is a certified ArchiMate practitioner and the additional
  governance layers ArchiMate provides become necessary.

## References

- Simon Brown, _The C4 Model for Visualising Software Architecture_, c4model.com
- ISO 27001:2022 Annex A, Control A.12.1 — Documented operating procedures
- EU AI Act (2024) Art. 13 — Transparency and provision of information to users
- `docs/adr/README.md` — ADR index and canonical template
- `specs/system/01-system-architecture.md` — L1/L2 diagram spec (to be authored, issue #9)
- CLAUDE.md §6 — ADR governance
