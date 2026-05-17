# ADR-0029: DPIA/RIPD Required Before Production Deployment

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / DPO / Privacy Lead — researcher)
**Affected RQs**: RQ4 (privacy compliance)

---

## Context

The Copilot is an Agentic AI system that processes personal data in the course of
incident response: observability data containing `user_id`, IP addresses and
request parameters; post-mortems with incident participant metadata; and LLM prompts
constructed from this data. When deployed in production handling real incident data,
this processing is systematic and large-scale.

Two legal obligations independently require a formal impact assessment before this
processing begins:

- **GDPR art. 35** — a Data Protection Impact Assessment (DPIA) is mandatory before
  processing that is "likely to result in a high risk to the rights and freedoms of
  natural persons", including systematic and large-scale processing of personal data
  using new technologies. An AI system that autonomously processes incident data
  clearly qualifies.
- **LGPD art. 38** — the Relatório de Impacto à Proteção de Dados Pessoais (RIPD) is
  required when processing is likely to generate risks to data subjects; ANPD may
  require it at any time.

CLAUDE.md §1.6 Success Criterion 4 is a hard project gate: _"DPIA/RIPD completed and
approved before any production release handling real incident data."_ This ADR defines
what "completed and approved" means operationally.

## Decision

**No production deployment handling real incident data proceeds without a completed,
reviewed and signed DPIA (GDPR art. 35) and RIPD (LGPD art. 38).**

The DPIA/RIPD is a hard release gate: `harness/release-check.yml` includes a manual
approval step that requires the DPO/Privacy Lead to confirm the assessment is complete
before the release pipeline continues.

### DPIA/RIPD document structure

The assessment is stored in `specs/privacy/21-dpia-ripd.md` and must contain all
sections from both GDPR art. 35(7) and LGPD art. 38:

#### Part A — Processing description (GDPR art. 35(7)(a), LGPD art. 38 I)

| Section             | Required content                                                            |
| ------------------- | --------------------------------------------------------------------------- |
| Processing purposes | Specific purposes for each agent's data use                                 |
| Data categories     | Full PII inventory per `specs/privacy/19-pii-inventory.md`                  |
| Data flows          | C4 Level 2 diagram annotated with personal data flows                       |
| Retention periods   | Per ADR-0030 TTL policy                                                     |
| Recipients          | All processors: Anthropic API, observability backends, cloud storage        |
| Technical controls  | PII masking (ADR-0014), sanitization (ADR-0028), encryption, access control |

#### Part B — Necessity and proportionality assessment (GDPR art. 35(7)(b))

- Why is each processing purpose necessary for incident response?
- Could a less privacy-intrusive approach achieve the same outcome?
- Is the data minimisation default (ADR-0027) documented and enforced?

#### Part C — Risk assessment (GDPR art. 35(7)(c), LGPD art. 38 II)

Risk register with likelihood × impact matrix for:

| Risk                                     | Likelihood | Impact | Mitigation                         |
| ---------------------------------------- | ---------- | ------ | ---------------------------------- |
| PII exposure via LLM prompt              | Medium     | High   | ADR-0028 (Presidio sanitization)   |
| PII in observability pipeline            | Medium     | High   | ADR-0014 (OTel masking)            |
| Audit trail compromise                   | Low        | High   | ADR-0024 (hash chain, append-only) |
| Cross-border transfer without safeguards | Low        | High   | ADR-0032 (SCCs)                    |
| Agent hallucination disclosing PII       | Low        | Medium | OWASP LLM06 mitigation (ADR-0021)  |

#### Part D — Measures to address risks (GDPR art. 35(7)(d))

Reference to all ADRs that implement privacy controls, with evidence that each control
is operational (unit test references, SAST gate confirmation, audit log samples).

#### Part E — DPO consultation record (GDPR art. 35(2))

For this research project: researcher acting as DPO confirms assessment. Date, scope
and sign-off recorded.

#### Part F — RIPD-specific fields (LGPD art. 38)

- Description of processing and legal basis per LGPD art. 7
- Legitimate interest assessment (if applicable)
- Measures, safeguards and risk mitigation mechanisms adopted

### Completion checklist

The DPIA/RIPD is considered complete when all of the following are checked:

- [ ] All six sections (A–F) authored and internally consistent
- [ ] PII inventory (`specs/privacy/19-pii-inventory.md`) referenced and complete
- [ ] All privacy ADRs (0027–0032) referenced as technical controls
- [ ] Risk register: no residual High risks without documented mitigation
- [ ] DPO/Privacy Lead sign-off recorded with date and scope
- [ ] Legal review completed (or waived with documented rationale for academic context)
- [ ] DPIA stored in `specs/privacy/21-dpia-ripd.md` and version-controlled

### Release gate integration

```yaml
# harness/release-check.yml (excerpt)
- name: DPIA/RIPD gate
  run: |
    if [ ! -f specs/privacy/21-dpia-ripd.md ]; then
      echo "BLOCKED: DPIA/RIPD document not found"
      exit 1
    fi
    python scripts/check_dpia_completeness.py specs/privacy/21-dpia-ripd.md
```

`check_dpia_completeness.py` verifies that all six sections are present and the
completion checklist has no unchecked items.

## Alternatives Considered

| Alternative                             | Pros                                                                   | Cons                                                                                             |
| --------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| **No DPIA/RIPD**                        | Zero overhead                                                          | GDPR art. 35 / LGPD art. 38 violated; potential regulatory action; CLAUDE.md criterion 4 not met |
| **DPIA only (GDPR)**                    | Simpler                                                                | LGPD art. 38 (RIPD) also applies — Brazilian data subjects are in scope                          |
| **Post-production DPIA**                | Later; less effort                                                     | Legally invalid — GDPR art. 35 requires assessment _before_ processing begins                    |
| **Full DPIA/RIPD before production** ✅ | Legal compliance; structured risk documentation; release gate enforced | Requires ~8–12 hours of researcher time for initial assessment; ongoing update per data change   |

## Consequences

**Positive:**

- CLAUDE.md §1.6 criterion 4: hard gate enforced — no accidental production deployment
  without the assessment.
- GDPR art. 35 and LGPD art. 38: documented, structured assessment with risk register
  and mitigation evidence — available for regulatory inspection.
- The structured risk register surfaces any privacy ADR gaps before production — acts
  as a final privacy architecture review.

**Negative / Trade-offs:**

- ~8–12 hours of researcher time for initial DPIA/RIPD authoring — scheduled in
  Phase 2 (issue #14) before any Phase 5 production deployment.
- Assessment must be updated for any material change to data processing scope —
  adds process overhead for new features that process personal data.

## Review Criteria

Revisit this decision if:

- ANPD publishes a RIPD template that requires different sections — update the
  document structure and this ADR.
- The dissertation scope changes to include new categories of personal data not
  covered by the current risk register.

## References

- GDPR (EU 2016/679) Art. 35 — Data protection impact assessment
- LGPD (Lei 13.709/2018) Art. 38 — Relatório de Impacto à Proteção de Dados
- EU AI Act (2024) Art. 9 — Risk management system (complementary)
- ANPD — Resolution CD/ANPD No. 2 (2022) — RIPD guidance
- `docs/adr/ADR-0027-privacy-by-design-sdlc.md` — PbD principle 5 (end-to-end security)
- `specs/privacy/21-dpia-ripd.md` — DPIA/RIPD document (to be authored, issue #14)
- `specs/privacy/19-pii-inventory.md` — PII inventory (prerequisite for DPIA)
- CLAUDE.md §1.6 criterion 4 — DPIA/RIPD hard gate before production
- `PRIVACY.md` — public data processing notice
