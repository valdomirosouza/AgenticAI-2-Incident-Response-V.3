# Spec 07: Release Process

**Domain**: sdlc
**Owner**: Engineering Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #10
**Linked ADRs**: ADR-0006, ADR-0009
**Review cadence**: Every major release or on deployment strategy change

---

## 1. Purpose

Define the end-to-end release process: SemVer versioning policy, release checklist,
CHANGELOG automation, blue-green deployment flow and rollback trigger conditions with
RTO targets.

---

## 2. Context

ADR-0006 governs Conventional Commits and SemVer bump rules. ADR-0009 governs
blue-green zero-downtime deployments with rollback < 30s. This spec translates both
into an operational release checklist and a documented rollback protocol.

Release Please (`.github/workflows/release-please.yml`) automates CHANGELOG updates
and version bumps from Conventional Commit messages on every push to `main`. This spec
defines what happens before, during and after Release Please creates a release PR.

---

## 3. Decision

### 3.1 SemVer versioning policy

Per ADR-0006:

| Commit type(s)                                | Version bump | Example       |
| --------------------------------------------- | ------------ | ------------- |
| `feat`                                        | MINOR        | 0.3.0 → 0.4.0 |
| `fix`, `security`, `perf`, `hotfix`           | PATCH        | 0.4.0 → 0.4.1 |
| Any type with `!` or `BREAKING CHANGE` footer | MAJOR        | 0.4.1 → 1.0.0 |
| `chore`, `test`, `ci`, `docs`, `refactor`     | No bump      | —             |

Pre-1.0.0: `feat` bumps MINOR (not MAJOR) per `bump-minor-pre-major: true` in
`release-please-config.json`.

### 3.2 CHANGELOG automation

Release Please manages the `[Unreleased]` section of `CHANGELOG.md` automatically:

1. Every Conventional Commit merged to `main` is appended to `[Unreleased]`.
2. When a release is triggered, Release Please opens a release PR that:
   - Renames `[Unreleased]` to `[<version>] — <date>`
   - Bumps `version.txt` to the new version
   - Creates a GitHub Release with the tag `v<version>`
3. The release PR is reviewed and merged by the Tech Lead.

**Manual `[Unreleased]` edits are prohibited** — they will be overwritten by Release Please.
Pre-automation entries remain in `[0.2.0-dev]` and `[0.1.0]` as historical records.

### 3.3 Pre-release checklist

Before merging the Release Please PR:

#### Automated gates (must all be green)

- [ ] All CI gates G01–G14 pass on the release branch
- [ ] DPIA/RIPD gate: `specs/privacy/21-dpia-ripd.md` exists and `check_dpia_completeness.py` passes (ADR-0029)
- [ ] OWASP LLM Top 10 release checklist artifact generated (ADR-0021)
- [ ] SBOM published; Grype CVE scan — zero unmitigated Critical CVEs (ADR-0019)
- [ ] Staging DAST scan (OWASP ZAP + Nuclei) — zero Critical/High findings (ADR-0018)
- [ ] Docker image Trivy scan — zero Critical CVEs in production image (ADR-0007 G14)

#### Manual gates (DPO / Tech Lead sign-off)

- [ ] Bias audit completed within last 90 days for TriageAgent and RCAAgent (ADR-0026)
- [ ] Kill-switch drill completed within last 90 days (ADR-0025)
- [ ] `PRIVACY.md` reflects current data processing activities
- [ ] `SECURITY.md` reflects current vulnerability disclosure scope
- [ ] All open High security findings have documented mitigations or accepted-risk entries
- [ ] Release notes reviewed: version bump is correct; CHANGELOG entries are accurate

### 3.4 Blue-green deployment flow

Per ADR-0009:

```
Current state: Blue slot serving 100% traffic

Step 1  Deploy new version to Green slot (idle)
        └─ Argo Rollouts creates Green ReplicaSet; runs smoke tests

Step 2  Smoke tests pass?
        YES → Step 3
        NO  → Abort; Green slot torn down; Blue continues (zero user impact)

Step 3  HITL drain: wait for in-flight requests to complete (max 30s)

Step 4  Switch: Argo Rollouts shifts 100% traffic to Green
        └─ Blue slot retained for rollback window (15 minutes)

Step 5  Post-switch health check (2 minutes)
        PASS → Blue slot torn down; release complete
        FAIL → Rollback (Step 6)

Step 6  Rollback: shift 100% traffic back to Blue (< 30s)
        └─ Incident created; PostMortemAgent drafts deployment post-mortem
```

### 3.5 Rollback trigger conditions and RTO

| Condition                                             | Automatic / Manual | RTO target                          |
| ----------------------------------------------------- | ------------------ | ----------------------------------- |
| Smoke tests fail during Green deployment              | Automatic          | < 10s (abort before traffic switch) |
| Post-switch health check fails (p99 latency > 2× SLO) | Automatic          | < 30s                               |
| Error rate > 5% within 2 minutes of cutover           | Automatic          | < 30s                               |
| On-call engineer triggers manual rollback             | Manual             | < 30s                               |
| Kill-switch activated (ADR-0025)                      | Manual / Automatic | < 60s                               |

Rollback is always available within the 15-minute Blue slot retention window. After 15
minutes the Blue slot is torn down and rollback requires a new deploy from the previous
release tag.

### 3.6 Post-release steps

1. Verify production health: Golden Signal dashboards stable for 15 minutes post-switch.
2. Close the Release Please PR merge event in GitHub (it auto-tags `v<version>`).
3. Archive SBOM artifact for the release (ADR-0019 — SBOM retained for release lifetime + 2 years).
4. Update `issues.md` if the release closes a phase milestone.
5. Notify stakeholders (dissertation advisor) of production release with release notes link.

---

## 4. Acceptance Criteria

- [ ] SemVer bump rules table covers all commit types including BREAKING CHANGE
- [ ] CHANGELOG automation section explains Release Please flow and prohibits manual edits
- [ ] Pre-release checklist covers both automated and manual gates; references ADR-0029 hard gate
- [ ] Blue-green deployment flow covers all 6 steps including smoke tests and HITL drain
- [ ] Rollback trigger conditions table covers 5 scenarios with RTO target for each
- [ ] Post-release steps include SBOM archival and health verification window
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                            |
| -------- | -------------------------------------------------------------------- |
| ADR-0006 | Conventional Commits — SemVer bump rules; CHANGELOG automation       |
| ADR-0007 | PR merge gates — automated gates required before release merge       |
| ADR-0009 | Blue-green deployment — zero-downtime flow; rollback < 30s RTO       |
| ADR-0018 | DAST — staging scan required before every release (pre-release gate) |
| ADR-0019 | CycloneDX SBOM — generated and archived per release                  |
| ADR-0021 | OWASP LLM Top 10 — release checklist artifact required               |
| ADR-0025 | Kill-switch — drill cadence; RTO < 60s                               |
| ADR-0026 | Bias audit — 90-day recency gate before release                      |
| ADR-0029 | DPIA/RIPD — hard production release gate                             |

---

## References

- CLAUDE.md §2.1 SDD Cycle
- `docs/adr/ADR-0006-conventional-commits-semver.md`
- `docs/adr/ADR-0009-blue-green-deployment-strategy.md`
- `.github/workflows/release-please.yml` — Release Please workflow
- `release-please-config.json` — commit-type to changelog-section mapping
- `specs/sdlc/06-pr-and-review-process.md` — PR gates upstream of release
