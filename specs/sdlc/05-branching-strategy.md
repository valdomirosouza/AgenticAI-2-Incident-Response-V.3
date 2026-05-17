# Spec 05: Branching Strategy

**Domain**: sdlc
**Owner**: Engineering Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #10
**Linked ADRs**: ADR-0005
**Review cadence**: Quarterly or on process change

---

## 1. Purpose

Define the trunk-based development branching rules, branch naming conventions and
branch protection policies that all contributors must follow.

---

## 2. Context

ADR-0005 adopted trunk-based development with a single long-lived branch (`main`).
Short-lived feature branches are the only branching pattern — no `develop`, `release/*`
or `hotfix/*` long-lived branches. This spec translates that ADR decision into
actionable naming rules and protection configuration.

---

## 3. Decision

### 3.1 Branch model

| Branch type | Pattern                  | Max lifetime | Merges into | Merge strategy |
| ----------- | ------------------------ | ------------ | ----------- | -------------- |
| Trunk       | `main`                   | Permanent    | —           | —              |
| Feature     | `feature/<issue>-<slug>` | 2 days       | `main`      | Squash merge   |
| Fix         | `fix/<issue>-<slug>`     | 1 day        | `main`      | Squash merge   |
| Hotfix      | `hotfix/<issue>-<slug>`  | 4 hours      | `main`      | Squash merge   |
| Docs        | `docs/<issue>-<slug>`    | 2 days       | `main`      | Squash merge   |
| Chore       | `chore/<issue>-<slug>`   | 2 days       | `main`      | Squash merge   |

**`<issue>`** is the GitHub issue number (required). **`<slug>`** is a short kebab-case
description of the work (2–4 words).

Examples:

```
feature/9-specs-system
fix/42-detection-agent-timeout
hotfix/51-vault-token-expiry
docs/15-adr-0033-new-pattern
chore/22-dependency-updates
```

### 3.2 Branch protection rules (`main`)

| Rule                                   | Setting                                  |
| -------------------------------------- | ---------------------------------------- |
| Require pull request before merging    | Enabled                                  |
| Required approvals                     | 1 (solo project: admin bypass permitted) |
| Dismiss stale reviews on new push      | Enabled                                  |
| Require status checks to pass          | Enabled (all G01–G14 gates)              |
| Require branches to be up to date      | Enabled                                  |
| Do not allow bypassing required checks | Disabled (admin bypass for solo project) |
| Restrict force-push                    | Enabled                                  |
| Restrict deletions                     | Enabled                                  |

### 3.3 Branch lifecycle rules

1. **Create from `main`**: always branch from the latest `main` — never from another feature branch.
2. **Keep short**: branches older than their max lifetime are stale and must be rebased or closed.
3. **One issue per branch**: a branch addresses exactly one issue. Split work if scope creeps.
4. **Delete after merge**: the branch is deleted automatically on squash merge (`--delete-branch`).
5. **Rebase, don't merge**: if `main` has moved ahead, rebase the feature branch — no merge commits.

### 3.4 Commit discipline on branches

Each commit on a feature branch must follow Conventional Commits (ADR-0006):

```
<type>(<scope>): <description>
```

The squash merge commit message is derived from the PR title, which must also follow
Conventional Commits. The PR title is what Release Please reads to update CHANGELOG.

### 3.5 Emergency hotfix flow

For P1 incidents requiring an immediate production fix:

```
1. Create hotfix/<issue>-<slug> from main
2. Fix with a single commit: hotfix(<scope>): <description>
3. Open PR — skip non-critical review steps but all CI gates still run
4. Admin merge after CI passes
5. Trigger production deploy (blue-green, ADR-0009)
6. Backport commit message to CHANGELOG manually if Release Please hasn't picked it up
```

Hotfix branches have a 4-hour lifetime. If the fix isn't ready in 4 hours, the
branch is closed and the work moves to a `fix/` branch with normal lifecycle.

---

## 4. Acceptance Criteria

- [ ] Branch type table covers all 6 patterns: trunk, feature, fix, hotfix, docs, chore
- [ ] Branch naming pattern requires issue number — no anonymous branches
- [ ] Max lifetime defined for each branch type
- [ ] Branch protection rules table is complete with all settings for `main`
- [ ] Emergency hotfix flow is documented with explicit CI gate requirement (no skip)
- [ ] Conventional Commits requirement referenced for squash merge message (ADR-0006)
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                        |
| -------- | ---------------------------------------------------------------- |
| ADR-0005 | Trunk-based development decision — single trunk, squash merge    |
| ADR-0006 | Conventional Commits — commit message format on branches and PRs |
| ADR-0007 | PR merge gates — all gates still run on hotfix branches          |
| ADR-0009 | Blue-green deployment — hotfix deploy flow                       |

---

## References

- CLAUDE.md §2.1 SDD Cycle
- `docs/adr/ADR-0005-trunk-based-development-branching.md`
- `docs/adr/ADR-0006-conventional-commits-semver.md`
- `specs/sdlc/06-pr-and-review-process.md` — PR rules that govern branch merges
- `specs/sdlc/07-release-process.md` — release flow that starts from `main`
