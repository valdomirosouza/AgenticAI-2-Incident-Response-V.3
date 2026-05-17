# ADR-0018: DAST Execution Required in Staging Before Release

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Security Lead — researcher)
**Affected RQs**: RQ1 (SDLC governance), RQ4 (security compliance)

---

## Context

Dynamic Application Security Testing (DAST) tests a running application by sending
malicious or anomalous inputs and observing responses. It detects vulnerability classes
that SAST cannot find because they only manifest at runtime: injection flaws in
composed query strings, authentication bypass, insecure deserialization responses,
and server-side request forgery (SSRF).

DAST must run against a live environment, which means it cannot run in the PR gate
(no running application at PR time). The staging environment is the appropriate target:
it mirrors production configuration, is isolated from production data, and is the last
gate before a release (ADR-0009 Blue-Green deployment).

PCI-DSS 11.3 requires penetration testing and dynamic security testing of all
internet-facing applications before deployment. OWASP ASVS (Application Security
Verification Standard) Level 2 requires dynamic testing as a verification requirement.

## Decision

DAST is a **mandatory, blocking** stage gate: no release proceeds to production unless
the DAST scan of the staging environment passes (zero Critical/High findings).

### DAST toolchain

| Tool                             | Scope                                            | Mode                                  | Config                      |
| -------------------------------- | ------------------------------------------------ | ------------------------------------- | --------------------------- |
| **OWASP ZAP** (Zed Attack Proxy) | All HTTP/REST API endpoints (`src/api/`)         | Automated baseline scan + active scan | `harness/zap-config.yml`    |
| **Nuclei**                       | Known CVE templates against all exposed services | Template-based active scan            | `harness/nuclei-templates/` |

### Scan execution sequence (in staging gate `harness/staging-check.yml`)

1. Deploy candidate release to Green environment (ADR-0009).
2. Run smoke tests to verify the application is responsive.
3. Execute OWASP ZAP baseline scan (passive — no active exploitation): captures
   information disclosure, missing headers, insecure cookies.
4. Execute OWASP ZAP active scan against the OpenAPI spec: tests injection, SSRF,
   broken authentication, path traversal.
5. Execute Nuclei CVE template scan.
6. Generate combined report (`dast-report-<version>.html`).
7. **Gate:** if any Critical or High finding is present → block release, create
   GitHub security advisory, notify Security Lead.
8. If clean: proceed to production traffic switch (ADR-0009).

### Scope

| In scope                        | Out of scope                                 |
| ------------------------------- | -------------------------------------------- |
| `src/api/` — all REST endpoints | Third-party APIs (Anthropic, Prometheus)     |
| Agent inbound HTTP adapters     | Internal gRPC (tested separately)            |
| HITL approval interface         | Infrastructure DAST (separate pentest scope) |

### Authenticated scanning

DAST scans run with a dedicated test service account (`dast-scanner@internal`).
This account has read-only access to the incident API and cannot trigger remediation
actions — preventing accidental production-impacting actions during the scan.

### False positive management

ZAP and Nuclei findings are reviewed by the Security Lead before blocking a release.
Known false positives are documented in `harness/dast-false-positives.yml` with an
expiry date (maximum 90 days); expired suppressions are re-evaluated.

## Alternatives Considered

| Alternative                               | Pros                                                                      | Cons                                                                                              |
| ----------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **No DAST**                               | Zero overhead                                                             | PCI-DSS 11.3 violated; runtime injection flaws undetected; OWASP ASVS Level 2 not met             |
| **Manual penetration test only**          | Human judgment; deeper coverage                                           | Not automated; cannot run before every release; too slow for the dissertation timeline            |
| **DAST in PR gate (against mock)**        | Earlier feedback                                                          | Mocks do not reflect real runtime behaviour; false negatives on integration-level vulnerabilities |
| **OWASP ZAP + Nuclei in staging gate** ✅ | Automated; runs against real application; blocks release on Critical/High | Adds ~10–15 minutes to staging gate — acceptable given release is not time-critical               |

## Consequences

**Positive:**

- Runtime vulnerabilities (SSRF, injection, auth bypass) caught before production.
- PCI-DSS 11.3 and OWASP ASVS Level 2 requirements satisfied.
- DAST report is an artifact attached to every release — provides audit evidence for
  security reviews and the dissertation appendix.
- Authenticated scanning with a read-only test account prevents accidental side effects.

**Negative / Trade-offs:**

- Staging gate duration increases by ~10–15 minutes — acceptable for a release process.
- OWASP ZAP active scan requires the OpenAPI spec (`src/api/openapi.yml`) to be
  current — stale spec produces incomplete scan coverage. Enforced by doc gate D02.

## Review Criteria

Revisit this decision if:

- False positive rate blocks releases more than twice per quarter — tune scan config
  before adding to the suppression list.
- A new API surface (gRPC, WebSocket) is introduced that ZAP cannot scan — evaluate
  additional DAST tools for that surface.

## References

- PCI-DSS v4.0 §11.3 — External and internal vulnerability scanning
- OWASP Application Security Verification Standard (ASVS) v4.0, Level 2
- OWASP ZAP — zaproxy.org; Nuclei — nuclei.projectdiscovery.io
- `docs/adr/ADR-0009-blue-green-deployment-strategy.md` — staging gate sequence
- `docs/adr/ADR-0017-sast-mandatory-pr-gate.md` — SAST (complementary to DAST)
- `harness/staging-check.yml` — staging gate config (to be authored, issue #21)
