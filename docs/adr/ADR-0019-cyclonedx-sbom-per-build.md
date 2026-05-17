# ADR-0019: CycloneDX SBOM Generated on Every Build

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Security Lead — researcher)
**Affected RQs**: RQ1 (SDLC governance), RQ4 (supply chain security)

---

## Context

A Software Bill of Materials (SBOM) is a formal, machine-readable inventory of all
components, libraries and dependencies that compose a software artifact. Two drivers
make SBOM generation mandatory for this project:

1. **SLSA Level 2** — requires that build provenance records the exact set of
   dependencies used to produce each artifact. An SBOM is the standard artifact
   for satisfying this requirement.
2. **US Executive Order 14028** (May 2021, "Improving the Nation's Cybersecurity")
   mandates SBOM for software sold to or used by the US federal government. While this
   project is academic, aligning with EO 14028 ensures the methodology is applicable
   to production deployments in regulated environments.
3. **CVE response time** — when a critical CVE is disclosed in a dependency (e.g.
   `requests`, `pydantic`, `anthropic`), the SBOM allows instant triage: is this
   dependency in our build? Which version? Which services?

Two SBOM standards exist: SPDX (Linux Foundation) and CycloneDX (OWASP). Both are
widely supported; the choice is made on tooling maturity for Python ecosystems.

## Decision

We adopt **CycloneDX v1.6** as the SBOM format. An SBOM is generated on every build
(PR gate and release gate) using **Syft** (Anchore) and attached as a build artifact.

### Generation toolchain

| Tool      | Role                                                          | Output                                 |
| --------- | ------------------------------------------------------------- | -------------------------------------- |
| **Syft**  | SBOM generation from Docker image and Python package manifest | `sbom-<service>-<version>.cdx.json`    |
| **Grype** | CVE scan against the generated SBOM                           | `vuln-report-<service>-<version>.json` |

### Generation points

| Trigger                | Gate                   | SBOM scope                             | Artifact stored in                   |
| ---------------------- | ---------------------- | -------------------------------------- | ------------------------------------ |
| Every PR (code change) | PR gate G11 (ADR-0007) | Python packages in `requirements.lock` | GitHub Actions artifact              |
| Every release          | Release gate           | Full Docker image (all layers)         | GitHub Release assets + OCI registry |

### SBOM fields (CycloneDX mandatory)

Each component entry must include:

- `name`, `version`, `purl` (Package URL — `pkg:pypi/<name>@<version>`)
- `licenses` — SPDX licence expression
- `hashes` — SHA-256 of the package distribution file
- `supplier` — package author/organisation

### CVE gate policy

After SBOM generation, Grype scans the SBOM against the NVD and OSV databases:

| CVE severity   | Gate action                                              |
| -------------- | -------------------------------------------------------- |
| **Critical**   | Blocks release (release gate) and PR gate G04 (ADR-0007) |
| **High**       | Blocks release; warning at PR gate                       |
| **Medium/Low** | Warning only; tracked in dependency backlog              |

### SBOM retention

- Build SBOMs (PR gate): retained for 90 days in GitHub Actions artifacts.
- Release SBOMs: retained for the life of the release + 2 years (aligned with audit
  log retention — ADR-0030).

## Alternatives Considered

| Alternative                  | Pros                                                                             | Cons                                                                                                   |
| ---------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **SPDX format**              | Linux Foundation standard; broader ecosystem                                     | Tooling for Python + Docker less mature than CycloneDX; OWASP Dependency-Track natively uses CycloneDX |
| **CycloneDX v1.6 + Syft** ✅ | Mature Python tooling; OWASP-backed; OCI registry support; Grype CVE scan native | Syft adds ~30s to build time — acceptable                                                              |
| **No SBOM**                  | Zero overhead                                                                    | SLSA Level 2 not met; EO 14028 alignment lost; CVE triage requires manual dependency audit             |
| **pip-audit only**           | Python-specific; fast                                                            | Does not cover Docker base image dependencies; not a full SBOM                                         |

## Consequences

**Positive:**

- SLSA Level 2 build provenance: every release has a signed SBOM attesting to exact
  dependency versions.
- CVE response time reduced: when a new CVE is disclosed, Grype immediately identifies
  affected services without manual audit.
- EO 14028 alignment: SBOM methodology applicable to production deployments in
  regulated environments.
- Release SBOMs attached to GitHub Releases — accessible to security auditors and
  dissertation reviewers.

**Negative / Trade-offs:**

- Syft adds ~30 seconds to CI; Grype adds ~20 seconds — total ~50s overhead per build.
- CycloneDX 1.6 is a recent version; some tooling may lag on schema support. Pin
  Syft version in CI to avoid unexpected format upgrades.

## Review Criteria

Revisit this decision if:

- OWASP updates CycloneDX to v2.0 with breaking changes — evaluate migration cost.
- SPDX becomes the mandated format for a specific compliance requirement — produce
  both formats using Syft's dual-output capability.

## References

- CycloneDX v1.6 — cyclonedx.org; Syft — github.com/anchore/syft; Grype — github.com/anchore/grype
- SLSA Level 2 — slsa.dev
- US Executive Order 14028 (2021) — Improving the Nation's Cybersecurity
- OWASP Dependency-Track — dependencytrack.org
- `docs/adr/ADR-0007-pr-merge-gates-ci-checks.md` — gate G11 (SBOM generation)
- `docs/adr/ADR-0022-dependency-pinning-cve-scanning.md` — dependency pinning complementing SBOM CVE scan
- `harness/code-check.yml` — G11 SBOM gate config (to be authored, issue #21)
