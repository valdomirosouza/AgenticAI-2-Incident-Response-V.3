# Spec 20: Data Retention Policy

**Domain**: privacy
**Owner**: DPO / Privacy Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #14
**Linked ADRs**: ADR-0030
**Review cadence**: Before every production deploy with PII changes; DPO + Legal required

---

## 1. Purpose

Define the TTL per data category, automated deletion mechanisms, manual deletion
procedure for data subject requests, and the audit evidence requirements that prove
retention compliance.

---

## 2. Context

ADR-0030 established explicit TTLs and automated deletion as the only compliant
retention model (LGPD art. 16, GDPR art. 5(1)(e) storage limitation). This spec
operationalises the ADR: where each TTL is configured, what deletes the data, who
is responsible, and what evidence must be produced for a DPIA/RIPD inspection.

---

## 3. Decision

### 3.1 Retention schedule

| Data category                    | Hot TTL               | Cold archive TTL           | Total max                     | Deletion mechanism                                    | Personal data?                 |
| -------------------------------- | --------------------- | -------------------------- | ----------------------------- | ----------------------------------------------------- | ------------------------------ |
| Application logs (Loki)          | 30 days               | +60 days                   | **90 days**                   | `retention_period: 90d` in Loki config                | Yes — pseudonymised `user_id`  |
| Distributed traces (Tempo)       | 14 days               | —                          | **14 days**                   | `--es.max-span-age=336h` Tempo flag                   | Yes — `user.id` pseudonymised  |
| Metrics time series (Prometheus) | 15 days (raw)         | 1 year (1m resolution)     | **1 year**                    | `--storage.tsdb.retention.time=15d` + recording rules | No (aggregated)                |
| Audit trail records (GCS)        | —                     | —                          | **2 years minimum**           | GCS Object Lifecycle rule: delete after 730 days      | Yes — pseudonymised roles      |
| Incident post-mortems            | Active + 90 days      | —                          | **90 days post-close**        | Automated archival + delete job                       | Yes — pseudonymised roles      |
| LLM prompt/response              | **Never persisted**   | —                          | Session only (in-memory)      | Not written to disk — by design                       | Yes — may contain residual PII |
| Research corpus (anonymised)     | Dissertation duration | —                          | Dissertation end + 5 years    | Manual secure deletion per PRIVACY.md                 | No (anonymised per spec 22)    |
| Research corpus (pseudonymised)  | Dissertation duration | —                          | **Dissertation end only**     | Automated deletion after thesis defence               | Yes — pseudonymised            |
| SBOM / build artifacts           | 90 days (PR)          | Release lifetime + 2 years | Release + 2 years             | GitHub Actions TTL + release cleanup                  | No                             |
| DPIA/RIPD document               | —                     | —                          | **Indefinite** (legal record) | Manual; requires DPO approval                         | No (no PII in doc itself)      |
| Vault audit logs                 | —                     | —                          | **2 years**                   | GCS lifecycle rule (same as audit trail)              | No (accessor IDs only)         |

### 3.2 Backend TTL configuration

Each TTL is configured in version-controlled infrastructure files, validated by Checkov
(ADR-0007 G05) to prevent silent TTL removal:

| Backend          | Config file                                 | TTL setting                                       |
| ---------------- | ------------------------------------------- | ------------------------------------------------- |
| Loki             | `infrastructure/loki/loki-config.yaml`      | `retention_period: 90d`                           |
| Tempo            | `infrastructure/tempo/tempo-config.yaml`    | `max_block_duration: 336h`                        |
| Prometheus       | `infrastructure/prometheus/prometheus.yaml` | `--storage.tsdb.retention.time=15d`               |
| GCS (audit)      | `infrastructure/gcs/lifecycle-audit.json`   | `{"age": 730, "action": {"type": "Delete"}}`      |
| GCS (vault logs) | `infrastructure/gcs/lifecycle-vault.json`   | `{"age": 730, "action": {"type": "Delete"}}`      |
| GitHub Actions   | `.github/workflows/*.yml`                   | `retention-days: 90` on all artifact upload steps |

All TTL configs are reviewed in the Pre-release checklist (spec 07) before every
production deploy. Any TTL reduction requires a new ADR.

### 3.3 LLM prompt non-persistence policy

LLM prompts and responses are **never written to any persistent storage**. They exist
only in process memory for the duration of the API call:

```python
# CORRECT — prompt lives only in function scope
def complete(self, prompt: str, *, sanitized: bool = False) -> str:
    if not sanitized:
        raise PiiSanitizationRequired(...)
    response = self._client.messages.create(model=..., messages=[{"role": "user", "content": prompt}])
    return response.content[0].text   # returned to caller; not stored

# PROHIBITED — would persist the prompt
self._prompt_cache[incident_id] = prompt   # blocked by Semgrep rule prompt-cache
```

Any caching of LLM outputs for latency reduction is prohibited without a separate ADR
that documents the legal basis, TTL and encryption-at-rest requirement.

### 3.4 Data subject deletion (erasure) procedure

LGPD art. 18 / GDPR art. 17 — response deadline: 15 days from verified request.

```
Step 1  DPO receives erasure request (email to valdomirojr@gmail.com)
Step 2  Verify identity of data subject (out-of-band confirmation)
Step 3  Identify user_id pseudonym(s) linked to the data subject
        (mapping table in Vault — never in repository)
Step 4  Delete or anonymise all records in each active data category:
        - Loki:   query by user_id label → delete matching log streams
        - Tempo:  query by user.id attribute → delete matching traces
        - Audit trail (GCS WORM): in-place replacement of user_id with [DELETED];
          record_hash recomputed; erasure-log record appended to chain
        - Post-mortems: redact pseudonymised role label linked to user
Step 5  Confirm: generate deletion evidence report
Step 6  Respond in writing to data subject within 15 days
Step 7  Record: create audit event audit.subject_erasure_completed
```

Audit trail records cannot be deleted (WORM storage) — only the `user_id` reference
within the payload is replaced. The hash chain integrity is preserved via the
erasure-log record appended in step 4.

### 3.5 Retention audit evidence

For DPIA/RIPD compliance inspections, the following evidence must be produced:

| Evidence item                               | Source                                               | Produced by     |
| ------------------------------------------- | ---------------------------------------------------- | --------------- |
| Loki retention config in effect             | `infrastructure/loki/loki-config.yaml`               | CI artifact     |
| Prometheus retention config in effect       | `infrastructure/prometheus/prometheus.yaml`          | CI artifact     |
| GCS Object Lifecycle rule JSON              | `infrastructure/gcs/lifecycle-audit.json`            | CI artifact     |
| LLM prompt non-persistence unit test result | `tests/unit/test_llm_adapter_no_cache.py`            | pytest report   |
| Last data subject erasure log (if any)      | Audit trail `audit.subject_erasure_completed` events | Audit API       |
| Research corpus deletion certificate        | Manual; DPO signs after thesis defence               | Manual document |

### 3.6 Privacy Impact

- Retention limits directly reduce LGPD art. 16 / GDPR art. 5(1)(e) exposure: data
  deleted automatically, not just on request.
- LLM prompt non-persistence eliminates the highest-risk persistent PII exposure path.
- Audit trail minimum retention (2 years) is a legitimate interest override of the
  storage limitation principle — documented in DPIA/RIPD (spec 21, Part B).
- Research corpus pseudonymised data is deleted immediately after thesis defence,
  regardless of the 5-year extension for anonymised data.

---

## 4. Acceptance Criteria

- [ ] Retention table covers all 11 data categories with hot TTL, cold TTL, total max and deletion mechanism
- [ ] LLM prompt non-persistence explicitly marked "Never persisted — Session only"
- [ ] Backend TTL configuration table maps each TTL to an infrastructure config file
- [ ] Data subject deletion procedure is 7 steps with 15-day response deadline
- [ ] Audit trail WORM constraint acknowledged: in-place `[DELETED]` replacement, not record removal
- [ ] Retention audit evidence table lists 6 evidence items for DPIA/RIPD inspection
- [ ] DPO / Privacy Lead + Legal review recorded before merge
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                               |
| -------- | ----------------------------------------------------------------------- |
| ADR-0024 | Immutable audit trail — WORM storage constraint on erasure              |
| ADR-0029 | DPIA/RIPD — retention schedule is Part A input (processing description) |
| ADR-0030 | Data retention TTL policy — authoritative TTL values                    |

---

## References

- LGPD (Lei 13.709/2018) Art. 16 — Retention and deletion; Art. 18 — Erasure right; Art. 19 — 15-day response
- GDPR (EU 2016/679) Art. 5(1)(e) — Storage limitation; Art. 17 — Right to erasure
- `docs/adr/ADR-0030-data-retention-ttl-policy.md`
- `specs/ethics/17-audit-trail.md` — WORM storage and erasure-log mechanism
- `specs/privacy/21-dpia-ripd.md` — retention schedule referenced in Part A
- `PRIVACY.md` — public retention notice
