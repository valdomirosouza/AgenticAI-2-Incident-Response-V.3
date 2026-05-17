# ADR-0032: Cross-Border Data Transfer Safeguards

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / DPO / Privacy Lead — researcher)
**Affected RQs**: RQ4 (privacy compliance)

---

## Context

The system sends data to services hosted outside Brazil and the EU/EEA:

1. **Anthropic Claude API** (ADR-0003) — LLM inference. Anthropic is a US company;
   data sent to its API crosses from Brazil (LGPD jurisdiction) and potentially from
   EU data subjects (GDPR jurisdiction) to the United States.
2. **Cloud observability backends** (if cloud-hosted) — Prometheus remote write,
   Loki, Tempo — may be hosted in US or EU regions depending on deployment.
3. **GitHub** (Actions, PRs, Issues) — CI/CD and code repository; US company.

Two legal frameworks regulate cross-border transfers:

- **GDPR art. 46** — transfers outside the EEA require one of the following safeguards:
  - Adequacy decision (US has no general adequacy decision post-Schrems II);
  - Standard Contractual Clauses (SCCs — EU Commission Decision 2021/914);
  - Binding Corporate Rules;
  - Derogations for specific situations (art. 49).
- **LGPD art. 33** — international transfers require either:
  - Transfer to a country with adequate protection (ANPD list, currently limited);
  - Contractual clauses or global corporate standards;
  - Specific consent of the data subject;
  - Research and academic cooperation (art. 33 VI).

For a research project, the **research and academic cooperation basis** (LGPD art. 33 VI)
provides a practical foundation for transfers necessary for the dissertation. However,
the **PII sanitization gate** (ADR-0028) is a technical control that minimises the
transfer risk regardless of the legal basis — by ensuring PII never reaches the
Anthropic API, the transfer risk is substantially reduced.

## Decision

The following cross-border transfer safeguards apply to each recipient:

### Transfer register

| Recipient                    | Country  | Data transferred                                                    | Legal basis (LGPD)                                                  | Legal basis (GDPR)                                           | PII present?                  |
| ---------------------------- | -------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------ | ----------------------------- |
| **Anthropic** (LLM API)      | USA      | Sanitized prompt text (no PII per ADR-0028); model ID; token counts | Art. 33 VI (research cooperation) + Art. 7 IX (legitimate interest) | SCCs (Module 1 — controller to processor) + Art. 89 research | No (PII stripped by ADR-0028) |
| **GitHub** (Actions/Pages)   | USA      | Source code, CI logs (no PII per RULE-C03); SBOM artifacts          | Art. 33 VI (research)                                               | SCCs (Module 1) + GitHub DPA                                 | No (RULE-C03 enforced)        |
| **Cloud provider** (GCP/AWS) | US or EU | Anonymised metrics, sanitized logs (if cloud-hosted)                | Art. 33 VI (research)                                               | SCCs (Module 1) if non-EU region; adequacy if EU region      | No (anonymised/sanitized)     |

### Anthropic-specific transfer safeguards

Anthropic provides a **Data Processing Agreement (DPA)** that incorporates SCCs
(EU Standard Contractual Clauses, 2021 edition) for EU data. For Brazilian data subjects
under LGPD, the research cooperation basis (art. 33 VI) applies, supplemented by:

1. **Technical control (primary):** PII sanitization via Presidio before every prompt
   (ADR-0028) — if no PII reaches the API, the transfer risk is effectively eliminated.
2. **Contractual control (secondary):** Anthropic DPA / Terms of Service — reviewed
   and accepted; includes data processing obligations and deletion commitments.
3. **Data minimisation:** only the minimum prompt context required for the reasoning
   task is sent — no full log dumps, only relevant excerpts.

### Transfer documentation

Each transfer relationship is documented in the DPIA/RIPD (ADR-0029):

- Recipient identity and country
- Legal basis with citation
- Technical control reducing transfer risk
- DPA / SCC reference

### Monitoring obligations

If a transfer basis changes (e.g. Anthropic changes DPA terms, ANPD publishes a new
adequacy list), the DPO reviews and updates this ADR and the DPIA/RIPD within 30 days.

The `PRIVACY.md` public notice references this ADR for transparency (GDPR art. 13/14,
LGPD art. 18 VIII — right to information about third-party sharing).

## Alternatives Considered

| Alternative                                              | Pros                                                                                                   | Cons                                                                                                                |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| **No documented safeguards**                             | Zero overhead                                                                                          | GDPR art. 46 / LGPD art. 33 violated; any supervisory authority inquiry finds no legal basis                        |
| **Explicit consent per transfer**                        | Clear legal basis                                                                                      | Impractical for incident response — no user interaction at transfer time                                            |
| **Only research basis (no technical controls)**          | Simple legal basis                                                                                     | Residual risk of PII in prompts if sanitization fails — defence in depth requires both legal and technical controls |
| **PII sanitization + documented SCCs/research basis** ✅ | Technical control (ADR-0028) eliminates PII before transfer; legal basis documented for each recipient | Requires DPA review and ongoing monitoring of provider terms                                                        |

## Consequences

**Positive:**

- GDPR art. 46 and LGPD art. 33 satisfied: each transfer has a documented legal basis
  and technical control.
- The combination of Presidio sanitization (ADR-0028) + SCCs means that even if the
  SCC legal basis is challenged, no PII is actually transferred.
- Transfer register is publicly referenced in `PRIVACY.md` — data subjects can exercise
  their right to information (LGPD art. 18 VIII) about third-party sharing.

**Negative / Trade-offs:**

- Requires ongoing monitoring of provider DPA terms — if Anthropic changes terms, the
  ADR and DPIA must be updated within 30 days.
- Post-Schrems II uncertainty for US transfers under GDPR means SCCs are the current
  best available mechanism but may be challenged — mitigated by the technical control
  making the legal question largely academic (no PII transferred).

## Review Criteria

Revisit this decision if:

- ANPD publishes an adequacy decision for the United States — switch LGPD basis from
  art. 33 VI to adequacy.
- The EU-US Data Privacy Framework (replacement for Privacy Shield) is invalidated
  again — re-evaluate the SCC basis and supplementary measures.
- The system adds a new external service recipient not listed in the transfer register.

## References

- LGPD (Lei 13.709/2018) Art. 33 — International data transfer; Art. 33 VI — Research basis
- GDPR (EU 2016/679) Art. 46 — Transfers subject to appropriate safeguards
- EU Commission Decision 2021/914 — Standard Contractual Clauses (SCCs)
- ANPD — Resolution CD/ANPD No. 19 (2024) — International transfer framework
- `docs/adr/ADR-0028-pii-sanitization-llm-apis.md` — PII sanitization (primary technical control)
- `docs/adr/ADR-0029-dpia-ripd-before-production.md` — DPIA must document each transfer
- `docs/adr/ADR-0030-data-retention-ttl-policy.md` — retention limits at recipient
- `PRIVACY.md` — public disclosure of transfers and data subject rights
