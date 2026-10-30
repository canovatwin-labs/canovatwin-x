# Changelog

All notable changes to CanovaTwin X are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
while it remains a research prototype (`0.x`: minor versions may change behaviour).

Two version numbers exist: the **application** version (`pyproject.toml`) and the
**analysis engine** version (`ENGINE_VERSION`), which guards replay compatibility
of stored analyses. The engine version only changes when diagnostic behaviour changes.

> The "Sprint N" labels below refer to the internal development sprints documented
> in `docs/SPRINT_N_REPORT.md`. They are different from the GitHub milestones
> (Sprint A1-A6, Phase B), which describe the academic and Canovate roadmap.

## [Unreleased]

### Added
- MIT `LICENSE`.
- `CODE_OF_CONDUCT.md` and this changelog.
- GitHub project management: milestones, labels, product backlog issues
  (US-01 to US-14) and the public roadmap board.

### Changed
- README licensing and distribution statement updated: the repository is public
  and released under the MIT License.
- Contribution and security documentation aligned with the public repository;
  MIT license metadata and distribution files included in Python packages.

### Fixed
- OpenAPI error descriptions no longer depend on Python's HTTP reason phrases;
  Python 3.12 now generates the same panel contract as Python 3.13 and 3.14.
- Added the missing repository handoff report linked from the README.

## [0.12.0] - 2026-10-30 (engine 0.4.0)

Sprint 11: recoverable, bounded offline telemetry journal.

### Added
- Transactional SQLite journal for append, drain, disconnect and reconnect.
- Hash-chained event sequence verified during startup; deterministic replay of
  pending data, committed window, watermark and connection state.
- Explicit concurrent-writer, corrupted-record, failed-write and event-limit
  failures, plus an installed-wheel recovery smoke test in CI.

### Notes
- This detects accidental corruption, not an attacker who can rewrite the
  database and hashes. No live gateway or automatic PLC connection is present.

## [0.11.0] - 2026-10-30 (engine 0.4.0)

Sprint 10: bounded event-time collector for offline telemetry replay.

### Added
- Explicit event-time and arrival-time handling, bounded out-of-order buffer,
  duplicate/late rejection, connection and freshness state, and a committed
  synthetic telemetry window for existing analysis contracts.
- Deterministic tests for ordering, backpressure, clock guards and reconnects.

### Notes
- No PLC transport, external dataset bypass, durable stream log or control
  command is included. The analysis engine and stored replay semantics are unchanged.

## [0.10.0] - 2026-10-30 (engine 0.4.0)

Sprint 9: provenance-bound exploratory review of declared external telemetry.

### Added
- A bounded CSV partition window adapter that retains absent channels as
  missing values and runs the existing deterministic core6 path after complete
  manifest validation.
- Explicit `declared_external` evidence provenance, `external_review` run mode,
  unknown-label status and mandatory human review even for clear results.
- An offline CLI review option; direct external claims through the HTTP analysis
  endpoint are rejected. Existing synthetic replay and evaluation stay intact.

### Notes
- Declared source and license remain unverified. No field diagnosis accuracy,
  actual external dataset, PLC access or actuator command is claimed.

## [0.9.0] - 2026-10-30 (engine 0.4.0)

Sprint 8: offline external dataset intake boundary.

### Added
- Strict manifest for declared source/license, CSV checksums, canonical channel
  units, expected sampling interval and asset/time-isolated splits.
- Bounded CSV validator with unit conversion, timestamp order, missing/out-of-range
  and gap counts, and normalized-content leakage checks across splits.
- `canovatwin-dataset` CLI with a non-overwriting JSON report. It does not fetch
  data, run diagnostics or present declared provenance as verified.

### Notes
- No independent dataset is bundled or scored. The analysis engine remains 0.4.0;
  no new agent, physical command or LLM call was introduced.

## [0.8.0] - 2026-10-30 (engine 0.4.0)

Sprint 7: reproducible synthetic evaluation foundation.

### Added
- Versioned seed-disjoint manifests with configuration/content leakage checks.
- Evaluation-only fault onset, severity, noise and missing-sensor variation.
- Independent threshold baseline alongside core6 and mvp12 comparisons.
- Per-case results, explicit alarm/candidate metrics, blocked-run coverage,
  latency, role count and model metrics; JSON/CSV/Markdown exports via `canovatwin-evaluate`.
- Installed-wheel evaluation smoke test in CI and 33 historical generator checksums.

### Notes
- This is a synthetic benchmark, not field validation, semantic RAG or learned ML.
- Node development requirements align with the merged jsdom 30 update.

## [0.7.0] - 2026-10-29 (engine 0.4.0)

Sprint 6: dynamic synthetic operation and a fuller investigation panel.

### Added
- Dynamic synthetic model: the 11 reference scenarios run with three workload
  profiles (steady, fluctuating, batch), slowly varying ambient conditions,
  fan time constant and sensor lag.
- Reproducible experiment metadata (generator version, scenario, conditions,
  sample count, seed) stored with each run. Fault labels and experiment settings
  are never passed to the specialists.
- Panel: schematic plant view, side-by-side temperature and load/cooling charts,
  fan command/feedback chart, scenario briefing and stale-measurement warnings.

### Changed
- Replay re-analyses stored inputs, policy and sources and preserves metadata;
  records written before this version remain readable.

### Verification
- 435 Python tests (branch coverage 97.85 %) and 39 frontend tests.
- 33 dynamic combinations (11 scenarios x 3 workload profiles) checked.
- These figures are software test results, not a diagnostic accuracy score.

## [0.6.0] - 2026-10-28 (engine 0.4.0)

Sprint 5: local investigation panel.

### Added
- Self-hosted React/TypeScript panel: overview, incidents, telemetry charts,
  evidence, execution traces and scenario configuration.
- Session roles with separate read and write credentials; credentials are kept in
  browser memory only and cleared on reload or logout.
- Strict serving headers (CSP, cache control) and safe handling of a missing build.

### Fixed
- Missing temperature values are no longer drawn as zero; time axis uses real
  time differences.
- Failed activation attempts are no longer counted as executed agents.
- Stale hashed assets could survive a repeated source install; packaging now
  regenerates the panel copy and `scripts/verify_package.py` checks it.

### Verification
- 364 Python tests (branch coverage 97.74 %) and 31 frontend tests.

## [0.5.0] - 2026-10-28 (engine 0.4.0)

Sprint 4: local HTTP API.

### Added
- Local FastAPI service with validated request/response contracts, OpenAPI
  export, loopback-only serving by default and separate read/write credentials.
- Safe error behaviour, connection and resource management.

### Verification
- 338 tests, including 96 new checks, a real HTTP smoke test and a clean-package check.

## [0.4.0] - 2026-10-28

Sprint 3: twelve-specialist offline MVP.

### Added
- Specialists A06 (missing data), B05 (historical case matching), B06
  (hypothesis critic), D02 (what-if design), D06 (model validation) and F02
  (cited keyword search over local demo notes). 12 of 36 registered roles are
  now implemented as deterministic specialists.

### Notes
- Retrieval is keyword based; semantic RAG and LLM orchestration are not implemented.
- What-if comparisons use an illustrative reduced model, not a calibrated one.

## [0.3.0] - 2026-10-28

Sprint 2: persistent analysis history.

### Added
- SQLite persistence with atomic writes, incident lifecycle, audit trail,
  optimistic revision checks and verified reads.
- Replay of stored inputs for reproducible re-analysis.

### Verification
- 181 tests passing.

## [0.2.0] - 2026-10-28

Sprint 1: adaptation to the original architecture.

### Added
- 36-role agent catalog with registry, permissions and bounded execution budgets.
- Time-series and data-quality checks, hypothesis and evidence chain, conditional
  routing and a synthetic cooling system.
- Reproducible development setup with locked dependencies.

[Unreleased]: https://github.com/canovatwin-labs/canovatwin-x/compare/main...HEAD
