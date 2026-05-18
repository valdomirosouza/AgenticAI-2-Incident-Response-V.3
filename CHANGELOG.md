# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Traceability rule:** every entry must reference the issue, ADR or PR that produced the change.
> **Automation note:** the `[Unreleased]` section is managed automatically by
> [Release Please](https://github.com/googleapis/release-please). Do not edit it manually.

---

## [0.6.0](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/compare/v0.5.2...v0.6.0) (2026-05-18)


### ### Added

* **changelog:** fix double-### heading in v0.5.2, add infrastructure entry, reposition [Unreleased] ([cd438e8](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/cd438e807e91755324e473c5b858e5771abe67fb))
* **lim:** add specs and pyproject scaffold — issue [#59](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/59) ([#69](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/69)) ([3c81e14](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/3c81e142fc66c898af523f61349f43adcd986d28))
* **lim:** ADRs 0033–0035 — LIM service layout, Redis sorted sets, exact ZRANK percentile ([#70](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/70)) ([ae4418b](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/ae4418bf6a9c464a4ec5ec3747d1fbb879b54f8e)), closes [#60](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/60)
* **lim:** domain models HaproxyLogEntry, MetricPoint, SignalType, AnalyticsResult ([#71](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/71)) ([ef2ddb8](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/ef2ddb88b5aa49a2bc4cb89ebe87c73abb9bb91b))
* **lim:** domain services LogParser + PercentileCalculator ([#72](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/72)) ([4b9c32e](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/4b9c32ef87f19a1c3eb090b1b21593f5d860c7f6))
* **lim:** GET /analytics router with exact percentile query ([#76](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/76)) ([e61b493](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/e61b493bbf7e76cd47c98fed07f10c12c905ca81))
* **lim:** hexagonal ports MetricStorePort + IngestionPort ([#73](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/73)) ([bff65a8](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/bff65a8851fdfde567ebd917d4d2b4d4bfd9d81b))
* **lim:** OTel instrumentation, Prometheus alerts, and Dockerfile — issue [#67](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/67) ([#77](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/77)) ([27ff68f](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/27ff68f83116fc640b9c2d2f714d7618d9b80be3))
* **lim:** POST /ingestion router + IngestionService + health endpoints ([#75](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/75)) ([6f34250](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/6f342504bade48007b750a18b904e0523275f5bd))
* **lim:** RedisMetricAdapter + error class encoding ([#74](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/74)) ([620cbed](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/620cbedd0965db6fa45330e677dc370d1de6b974))


### ### Fixed

* **ci:** add -R flag to gh run list calls to fix missing git context ([2283cfc](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/2283cfc48fe471533c796fb387f34d0a8827c18e))
* **ci:** add missing .semgrep/ custom rule files (G06-G09) ([4b2d767](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/4b2d76744f7fa204edffc17a820eb045a151dbcc))
* **ci:** generate requirements.lock with Linux x86_64 hashes ([b460075](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/b46007566fbdbd292522c1c1edb6c77f37ebc62b))
* **ci:** quote cd-staging workflow_dispatch description to fix YAML syntax error ([4749d80](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/4749d801a67be0b809a3eb2206ffd5cb5d2c5089))
* **ci:** replace invalid setup-python SHA with v5.6.0 ([4a496ca](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/4a496cac7ccfa7f5577ae9fd6d4245bb7fefeeaf))
* **ci:** replace status-snapshot check with gh run watch to handle in-progress CI ([5d824a4](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/5d824a4cbd1451fc6b6a3037860b5f7c21932a38))

## [Unreleased]

---

## [0.7.0](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/compare/v0.6.7...v0.7.0) (2026-05-17)

### Added

- **lim:** Phase 7 [E2] — 10 end-to-end integration tests in `tests/integration/test_pipeline_integration.py` against in-process FakeRedis (no Docker): round-trip traffic + RPS, error rate, saturation, latency P50/P99, signal filtering (traffic-only, error-only), multi-path aggregation, single-path isolation, partial failure resilience — issue [#68](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/68) ([#78](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/pull/78)) ([5e64ab6](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/5e64ab6))
- **ci:** `lim-service` job in `.github/workflows/ci.yml` — runs unit tests (G01), integration tests (G01), coverage ≥ 80 % (G02), mypy strict (G12), import-linter hexagonal (G13) for the LIM sub-project — issue [#68](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/68) ([#78](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/pull/78))
- **harness:** 4 LIM-specific gates in `harness/code-check.yml`: `LIM-G01` (unit + integration tests), `LIM-G02` (branch coverage ≥ 80 %), `LIM-G12` (mypy strict), `LIM-G13` (import-linter hexagonal); all gates binary and blocking — issue [#68](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/68) ([#78](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/pull/78))
- **lim:** Total LIM test suite: **230 tests passing** (220 unit + 10 integration); 3 import-linter contracts green (domain independence, ports independence, adapters no-API)

---

## [0.6.7](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/compare/v0.6.6...v0.6.7) (2026-05-17)

### Added

- **lim:** Phase 7 [E1] — OTel instrumentation: `observability/metrics.py` with `configure(otlp_endpoint)`, `lim_ingestion_events_total` counter (labels: `backend`, `result`), `lim_ingestion_batches_total` counter (label: `size_bucket`), `lim_analytics_query_seconds` histogram (labels: `signal`, `window`, `result`); wired into `POST /ingestion` and `GET /analytics` routers; `OTLP_ENDPOINT` env var drives MeterProvider at lifespan startup — issue [#67](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/67) ([#77](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/pull/77)) ([27ff68f](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/27ff68f))
- **lim:** Multi-stage `Dockerfile`: Python 3.12 slim builder + runtime, non-root `lim` user, `/health/live` `HEALTHCHECK` — issue [#67](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/67) ([#77](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/pull/77))
- **lim:** `log-ingestion-alerts.yaml` — 5 Prometheus alert rules: `LimHighStoreErrorRate` (critical, > 5 %), `LimHighParseErrorRate` (warning, > 10 %), `LimIngestionSilent` (warning, no batches 10 min), `LimAnalyticsHighLatency` (warning, P95 > 1 s), `LimAnalyticsHighMissRate` (warning, > 20 % 404) — issue [#67](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/67) ([#77](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/pull/77))
- **lim:** 24 new unit tests in `test_observability_metrics.py`; total LIM test suite: **220 tests passing**

---

## [0.6.6](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/compare/v0.6.5...v0.6.6) (2026-05-17)

### Added

- **lim:** Phase 7 [D2] — `GET /analytics` router: single-path and multi-path aggregation (SCAN + ZUNIONSTORE), exact latency percentiles via `PercentileCalculator` (ADR-0035), signal filtering, 404/422 semantics; 196 unit tests green — issue [#66](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/66) ([#76](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/pull/76)) ([e61b493](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/e61b493))

---

## [0.6.5](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/compare/v0.6.4...v0.6.5) (2026-05-17)

### Added

- **lim:** Phase 7 [D1] — `POST /ingestion` router (partial-failure semantics, 1 000-entry cap, errors capped at 10), `IngestionService` (orchestrates `LogParser` + `MetricStorePort` in a single `store_batch` call), `GET /health/live` + `GET /health/ready`, FastAPI app with lifespan; 169 unit tests green — issue [#65](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/65) ([#75](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/pull/75)) ([6f34250](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/6f34250))

---

## [0.6.4](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/compare/v0.6.3...v0.6.4) (2026-05-17)

### Added

- **lim:** Phase 7 [C2] — `RedisMetricAdapter`: concrete `MetricStorePort` backed by redis-py asyncio client; atomic pipeline writes; URL-encoded key segments; ADR-0030 TTLs (latency 86 400 s, counters 604 800 s); 136 unit tests green — issue [#64](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/64) ([#74](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/pull/74)) ([620cbed](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/620cbed))

### Changed

- **lim:** `LogParser._error_value` encodes error class in `MetricPoint.value` (`4.0` = 4xx → `lim:err4`, `5.0` = 5xx/abnormal → `lim:err5`, `0.0` = clean) to enable Redis key routing without carrying `status_code` through the domain boundary

---

## [0.6.3](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/compare/v0.6.2...v0.6.3) (2026-05-17)

### Added

- **lim:** Phase 7 [C1] — hexagonal port ABCs: `MetricStorePort` (8 async Redis operations) and `IngestionPort` + `IngestionResult` (driving port, partial-failure semantics, error cap 10); 103 unit tests green — issue [#63](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/63) ([#73](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/pull/73)) ([bff65a8](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/bff65a8))
- **docs:** service README for `log-ingestion-and-metrics` — pipeline diagram, API reference, architecture, ADR links, implementation status

---

## [0.6.2](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/compare/v0.6.1...v0.6.2) (2026-05-17)

### Added

- **lim:** Phase 7 [B2] — domain services: `LogParser` (4 Golden Signal MetricPoints per window, path extraction, error/saturation classification) and `PercentileCalculator` (exact ZRANK rank formula — ADR-0035); 80 unit tests green — issue [#62](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/62) ([#72](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/pull/72)) ([4b9c32e](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/4b9c32e))

---

## [0.6.1](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/compare/v0.6.0...v0.6.1) (2026-05-17)

### Added

- **lim:** Phase 7 [B1] — domain models: `HaproxyLogEntry`, `MetricPoint`, `SignalType`, `AnalyticsResult`; 34 unit tests green — issue [#61](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/61) ([#71](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/pull/71)) ([ef2ddb8](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/ef2ddb8))
- **chore:** root `.gitignore` — excludes `__pycache__`, `.venv`, `.coverage`, `.mypy_cache`

---

## [0.6.0](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/compare/v0.5.3...v0.6.0) (2026-05-17)

### Added

- **lim:** Phase 7 [A2] — ADRs 0033–0035: LIM service layout, Redis Sorted Sets for latency storage, exact ZRANK percentile algorithm — issue [#60](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/60) ([#70](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/pull/70)) ([ae4418b](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/ae4418b))

---

## [0.5.3](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/compare/v0.5.2...v0.5.3) (2026-05-17)

### Added

- **lim:** Phase 7 [A1] — LIM sub-project scaffold: specs (analytics-api, log-ingestion-api) and service pyproject.toml — issue [#59](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/59) ([#69](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/pull/69)) ([3c81e14](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/3c81e14))

---

## [0.5.2](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/compare/v0.5.1...v0.5.2) (2026-05-17)

### Added

- **infrastructure:** scaffold IaC — terraform, helm, monitoring — issue [#25](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/25) ([#56](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/56)) ([3639ad1](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/3639ad1))

### Fixed

- **changelog:** fix double-### heading in v0.5.1, add test suite entry, reposition [Unreleased] ([2853e83](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/2853e836439401edd80e2278f35148b60daaa647))

---

## [0.5.1](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/compare/v0.5.0...v0.5.1) (2026-05-17)

### Added

- **tests:** scaffold test suite — unit, integration, e2e, security, fixtures — issue [#24](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/24) ([#54](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/54)) ([f03d608](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/f03d608))

### Fixed

- **changelog:** fix double-### headings in v0.5.0–v0.3.0, reposition [Unreleased] to top ([9b680bb](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/9b680bb49e37c2b15db0264b1f5e1eedad667c5a))

---

## [0.5.0](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/compare/v0.4.0...v0.5.0) (2026-05-17)

### Added

- **ci:** add GitHub Actions CI/CD workflows — issue [#22](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/22) ([#51](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/51)) ([8970615](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/8970615fca1e5d501b8c821b5b2cf243cc770933))
- **harness:** add harness gate configuration files — issue [#21](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/21) ([#49](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/49)) ([bd8a3ba](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/bd8a3bacefe3859182b56a7750bca805f7ecb174))
- **src:** scaffold application source — hexagonal architecture, agents, guardrails — issue [#23](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/23) ([#52](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/52)) ([fae092c](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/fae092cac448cf6f838cf32ecb3a1cc988be7ed1))

## [0.4.0](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/compare/v0.3.0...v0.4.0) (2026-05-17)

### Added

- **skills:** add DevSecOps skills library (issue [#19](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/19)) ([#46](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/46)) ([fb6d14e](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/fb6d14ea9b2ccededef4f8e288e1929559cf0707))
- **skills:** add ethics and privacy skills — issue [#20](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/20) ([#48](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/48)) ([6a486c5](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/6a486c5c56d5ba9fc5faebb71de86a2a583060d7))

## [0.3.0](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/compare/v0.2.0...v0.3.0) (2026-05-17)

### Added

- **changelog:** fix structure — move [Unreleased] to top, remove duplicate entries, fix double-### headings ([0b417b6](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/0b417b630a79c47231a121cd3d0920893b35d7f8))
- **skills:** add observability skills library for issue [#18](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/18) ([#45](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/45)) ([e8ee8f6](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/e8ee8f6bf4ec268d645045c4fee02a69ecaeb9c2))
- **skills:** add SDLC skills library for issue [#17](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/17) ([#44](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/44)) ([ec8aa1e](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/ec8aa1eab77d8f0ec976e6b535f9840ee18babe4))
- **skills:** add writing and engineering skills for issue [#16](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/16) ([#42](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/42)) ([bb1b13a](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/bb1b13a0b50e592bbe155eaabe90e40ceae400f5))

### Fixed

- **ci:** add continue-on-error to claude-review job ([1d5caf2](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/1d5caf22c87e92343fc7dadf3fd30bdea359e5d8))

---

## [0.2.0](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/compare/v0.1.0...v0.2.0) (2026-05-17)

### Added

- add CLAUDE.md with project guidance for Claude Code ([1f19292](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/1f19292b15a72f54bafdfb72dc09fae611f07344))
- add issues.md backlog index and reference it in CLAUDE.md ([c397e3c](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/c397e3c6d207dd25891d62dd29952b19abb3d13d))
- add project README and skills library ([6f4b8e7](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/6f4b8e78f80e5f10daa07c9abe1009c948187618))
- **adr:** architecture & design ADRs 0001–0004 — issue [#3](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/3) ([#27](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/27)) ([6a3f787](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/6a3f787f7e88eaae3b39fdd5da47f5f0c035b056))
- **adr:** DevSecOps & security ADRs 0016–0022 — issue [#6](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/6) ([#30](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/30)) ([5fb14d1](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/5fb14d1ab4a49468443b39c3b671f1186a79e756))
- **adr:** Ethics & AI Governance ADRs 0023–0026 — issue [#7](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/7) ([#32](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/32)) ([22d097b](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/22d097b389e4310ded22e53bc12857d1b47a0242))
- **adr:** observability ADRs 0011–0015 — issue [#5](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/5) ([#29](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/29)) ([cbce4ea](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/cbce4ea8ce395ebad5f8e57e7b61b99dce1ba8bc))
- **adr:** SDLC & engineering ADRs 0005–0010 — issue [#4](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/4) ([#28](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/28)) ([a733748](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/a7337481f064384a07a449169c71a39a6d8f7dec))
- expand CLAUDE.md with authoring workflow and conventions ([4c5665e](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/4c5665efc7ce6ec224789a7e93b0c60fe82c9cf5))
- **privacy:** add ADR-0027 to ADR-0032 — Privacy & Data Protection ([#33](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/33)) ([a711f96](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/a711f9697d1e5d7c22fcda01813d00248e84ad61))
- rewrite README with full project description, problem statement and roadmap ([8eb5ccd](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/8eb5ccd4fdf94c93b914322c2daca257f0619e92))
- **skills:** add domain skills for agentic AI, incident lifecycle, MTTD/MTTR, and guardrails ([#41](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/41)) ([0c54df8](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/0c54df8c9992ea8c735590c56b4d8da721682e97))
- **specs:** add ethics domain specs 16–18 (issue [#13](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/13)) ([#39](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/39)) ([6afa269](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/6afa2691df249196e5d6dc73c3229abccd4a8c02))
- **specs:** add observability domain specs 08–11 (issue [#11](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/11)) ([#36](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/36)) ([3aea2db](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/3aea2db30089261a15562651eac7972ef538ac9e))
- **specs:** add privacy domain specs 19–22 (issue [#14](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/14)) ([#40](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/40)) ([5d0efba](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/5d0efba68a589d576033b7db789f3ff9e5ba3f4e))
- **specs:** add SDLC domain specs 04–07 (issue [#10](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/10)) ([#35](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/35)) ([c08f385](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/c08f385245099f68906c98acb64825e98c09125a))
- **specs:** add security domain specs 12–15 (issue [#12](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/12)) ([#38](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/38)) ([492a50f](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/492a50fa43f617fb0f84faa8981edd249b1f7e33))
- **specs:** add system domain specs 00–03 (issue [#9](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/9)) ([#34](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/34)) ([2ca1109](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/2ca110939a027fd8bb276979384151367d4f5d07))

### Fixed

- **ci:** enable Actions PR creation + opt into Node.js 24 for release-please ([9c55dfd](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/9c55dfdc976917010bbd24879405f7aacad766fd))

### Changed

- split CLAUDE.md into focused reference files to stay under 40KB ([913a200](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/commit/913a20053c68cf191cff6fe9464fc49a618d3b66))

---

## [0.2.0-dev] — 2026-05-17

> Phase 0 bootstrap + Phase 1 ADR batch (issues #2–#6). Pre-automation record.
> From v0.2.0 onwards, Release Please generates changelog entries from Conventional Commits.

### Added

- `docs/adr/ADR-0016` – `ADR-0022` — DevSecOps & Security ADRs: STRIDE, SAST, DAST, SBOM, Vault, OWASP LLM Top 10, dependency pinning (issue #6, PR #30)
- `docs/adr/ADR-0011` – `ADR-0015` — Observability ADRs: Golden Signals, OpenTelemetry, JSON logging, PII masking, SLO alerting (issue #5, PR #29)
- `docs/adr/ADR-0005` – `ADR-0010` — SDLC & Engineering ADRs: trunk-based dev, Conventional Commits, PR gates, coverage thresholds, Blue-Green, blameless post-mortem (issue #4, PR #28)
- `docs/adr/ADR-0001` – `ADR-0004` — Architecture & Design ADRs: C4 Model, Hexagonal Architecture, LLM selection, multi-agent orchestration (issue #3, PR #27)
- Branch protection on `main`: PR required, 1 approval, no force-push (issue #2, PR #26)
- `.github/pull_request_template.md` with author and reviewer checklists (issue #2, PR #26)
- `docs/glossary.md` with canonical 53-term project glossary (issue #2, PR #26)
- `SECURITY.md` vulnerability disclosure policy (issue #2, PR #26)
- `PRIVACY.md` data processing notice — LGPD art. 48, GDPR art. 33 (issue #2, PR #26)

---

## [0.1.0] — 2026-05-17

### Added

- `CLAUDE.md` v1.2.0 — behavioral contract for Claude Code: 8-pillar architecture, SDD cycle,
  harness rules, skill activation table, canonical glossary, 10-step workflow (PR #1-equivalent)
- `specs/README.md` — spec hierarchy: 22 spec files across 6 domains with per-file descriptions
- `docs/adr/README.md` — canonical ADR template + index of all 32 foundational ADRs
- `docs/repo-structure.md` — full annotated directory tree
- `skills/README.md` — 12 enterprise-grade shared skills library
- `skills/project-skills-catalog.md` — catalog of 30+ planned project-specific skills
- `issues.md` — 24-issue implementation backlog organized in 6 phases with dependency graph
- `README.md` — full project description: problem statement, solution, architecture, roadmap
- GitHub Issues #2–#25 — 24 documented issues with acceptance criteria and cross-references
- GitHub Milestones — 6 milestones (one per implementation phase)
- GitHub Labels — 14 labels (`phase:`, `type:`, `priority:`)
- `.github/workflows/` — Claude Code Review and Claude PR Assistant workflows (PR #1)
