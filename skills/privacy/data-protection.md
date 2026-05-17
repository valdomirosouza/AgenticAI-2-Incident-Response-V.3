# Skill: Data Protection

**Domain**: privacy
**Activation triggers**: Privacy by Design, data retention, TTL, deletion, encryption, RBAC, storage limitation, data minimisation, LLM prompt persistence, WORM, GCS, retention schedule, secure deletion
**References**: specs/privacy/20-data-retention-policy.md, ADR-0027, ADR-0030

---

## Privacy by Design Principles (ADR-0027)

| Principle                       | Implementation                                                                       |
| ------------------------------- | ------------------------------------------------------------------------------------ |
| **Proactive, not reactive**     | PII masking at collection point (OTel SpanProcessor) — not at query time             |
| **Privacy as default**          | Data minimisation: only minimum prompt context sent to LLM; no full log dumps        |
| **Privacy embedded in design**  | Presidio gate is architectural — `LLMAdapter.complete()` requires `sanitized=True`   |
| **Full functionality**          | Masking preserves MTTD/MTTR measurement utility (utility ≥ 80% threshold in spec 22) |
| **End-to-end security**         | TLS 1.3 in transit; AES-256 at rest (GCS); HMAC-SHA256 for ApprovalToken             |
| **Visibility and transparency** | PRIVACY.md public notice; DPIA/RIPD version-controlled; DPO contact published        |
| **Respect for user privacy**    | Data subject rights exercisable within 15 days; pseudonymisation by default          |

---

## Retention Schedule

| Data category                    | Hot TTL               | Cold archive  | Total max              | Deletion mechanism                          | Personal data?                 |
| -------------------------------- | --------------------- | ------------- | ---------------------- | ------------------------------------------- | ------------------------------ |
| Application logs (Loki)          | 30 days               | +60 days      | **90 days**            | `retention_period: 90d` in Loki config      | Yes — `user_id` pseudonymised  |
| Distributed traces (Tempo)       | 14 days               | —             | **14 days**            | `--es.max-span-age=336h` Tempo flag         | Yes — `user.id` pseudonymised  |
| Metrics time series (Prometheus) | 15 days raw           | 1yr (1m res)  | **1 year**             | `--storage.tsdb.retention.time=15d`         | No (aggregated)                |
| Audit trail records (GCS)        | —                     | —             | **2 years minimum**    | GCS Object Lifecycle: delete after 730 days | Yes — pseudonymised roles      |
| Incident post-mortems            | Active + 90d          | —             | **90 days post-close** | Automated archival + delete job             | Yes — pseudonymised roles      |
| LLM prompt/response              | **Never persisted**   | —             | Session only           | Not written to disk — by design             | Yes — may contain residual PII |
| Research corpus (anonymised)     | Dissertation duration | —             | Dissertation + 5 years | Manual secure deletion per PRIVACY.md       | No (anonymised)                |
| Research corpus (pseudonymised)  | Dissertation duration | —             | **Dissertation only**  | Automated deletion after thesis defence     | Yes — pseudonymised            |
| SBOM / build artifacts           | 90 days (PR)          | Release + 2yr | Release + 2 years      | GitHub Actions TTL + release cleanup        | No                             |
| DPIA/RIPD document               | —                     | —             | **Indefinite**         | Manual; DPO approval required               | No                             |
| Vault audit logs                 | —                     | —             | **2 years**            | GCS lifecycle rule                          | No (accessor IDs only)         |

---

## Backend TTL Configuration

Each TTL is version-controlled in infrastructure files, validated by Checkov (CI gate G05):

| Backend          | Config file                                 | TTL setting                                       |
| ---------------- | ------------------------------------------- | ------------------------------------------------- |
| Loki             | `infrastructure/loki/loki-config.yaml`      | `retention_period: 90d`                           |
| Tempo            | `infrastructure/tempo/tempo-config.yaml`    | `max_block_duration: 336h`                        |
| Prometheus       | `infrastructure/prometheus/prometheus.yaml` | `--storage.tsdb.retention.time=15d`               |
| GCS (audit)      | `infrastructure/gcs/lifecycle-audit.json`   | `{"age": 730, "action": {"type": "Delete"}}`      |
| GCS (vault logs) | `infrastructure/gcs/lifecycle-vault.json`   | `{"age": 730, "action": {"type": "Delete"}}`      |
| GitHub Actions   | `.github/workflows/*.yml`                   | `retention-days: 90` on all artifact upload steps |

**Any TTL reduction requires a new ADR** — TTL changes are architectural decisions (CLAUDE.md §6.1).

---

## LLM Prompt Non-Persistence Policy

LLM prompts and responses exist **only in process memory** for the duration of the API call:

```python
# CORRECT — prompt lives only in function scope; never stored
def complete(self, prompt: str, *, sanitized: bool = False) -> str:
    if not sanitized:
        raise PiiSanitizationRequired(
            "Call pii_sanitizer.sanitize() first, then pass sanitized=True"
        )
    response = self._client.messages.create(
        model=self._model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text  # returned to caller; not stored

# PROHIBITED — would persist the prompt
self._prompt_cache[incident_id] = prompt   # Semgrep rule prompt-cache detects this
```

Any prompt caching for latency is prohibited without an ADR documenting: legal basis, TTL, and encryption-at-rest requirement.

---

## Encryption Requirements

| Data state    | Algorithm   | Scope                                 | Implementation         |
| ------------- | ----------- | ------------------------------------- | ---------------------- |
| At rest       | AES-256     | GCS audit trail, Loki, Tempo, Vault   | GCS default + platform |
| In transit    | TLS 1.3     | All API endpoints and service calls   | Platform-enforced      |
| ApprovalToken | HMAC-SHA256 | HITL token signature (Vault key S-02) | `action_executor.py`   |
| Hash chain    | SHA-256     | Audit trail tamper-evidence           | `audit_adapter.py`     |

---

## RBAC — Access Control by Data Store

| Store           | Read                                            | Write                     | Delete                |
| --------------- | ----------------------------------------------- | ------------------------- | --------------------- |
| Loki (logs)     | SRE on-call, Tech Lead                          | OTel pipeline (automated) | TTL rule only         |
| Tempo (traces)  | SRE on-call, Tech Lead                          | OTel pipeline (automated) | TTL rule only         |
| Audit trail     | Tech Lead, SRE on-call                          | `audit_adapter` svc only  | **Impossible** (WORM) |
| Vault secrets   | `audit_adapter`, `llm_adapter` (own paths only) | DPO/Tech Lead             | DPO only              |
| Research corpus | Tech Lead, dissertation author                  | Anonymization pipeline    | Post-defence only     |

No DELETE endpoint exists on the audit trail API (spec 17 §3.5). GCS admin role is not granted to any service account in the Copilot deployment.

---

## Data Subject Deletion (Erasure) Procedure

Response deadline: **15 days** from verified request.

```
Step 1  DPO receives erasure request → valdomirojr@gmail.com
Step 2  Verify identity out-of-band
Step 3  Identify user_id pseudonym(s) — Vault mapping table (never in repo)
Step 4  Delete in each active store:
        Loki:         query label user_id=<hash> → delete matching streams
        Tempo:        query user.id=<hash> → delete matching traces
        Audit trail:  replace user_id with [DELETED] in payload (WORM constraint)
                      recompute record_hash; append erasure-log record to chain
        Post-mortems: redact pseudonymised role label linked to user
Step 5  Generate deletion evidence report
Step 6  Respond in writing to data subject within deadline
Step 7  Emit audit.subject_erasure_completed event
```

---

## Pre-Release Retention Checklist

Verify before every production deployment:

- [ ] Loki `retention_period: 90d` present in `infrastructure/loki/loki-config.yaml`
- [ ] Tempo `max_block_duration: 336h` set
- [ ] Prometheus `retention.time=15d` set
- [ ] GCS lifecycle rule for audit trail age=730 present and validated by Checkov
- [ ] GitHub Actions `retention-days: 90` on all artifact upload steps
- [ ] LLM prompt non-persistence unit test passes (`tests/unit/test_llm_adapter_no_cache.py`)
- [ ] No new indefinite-retention data stores introduced without ADR
