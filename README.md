# CanovaTwin X

**A simulation-first digital twin for data-center cooling and environmental monitoring.**

CanovaTwin X turns telemetry into traceable diagnostic reports. It combines a
reduced thermal model, deterministic specialist roles, evidence verification,
and a local investigation workspace. The current release runs entirely on
synthetic data, without cloud services or LLM calls.

Developed within **CanovaTwin Labs**. Current application: **0.14.0** ·
Analysis engine: **0.4.0** · Status: **research prototype**.

[Current status](docs/PROJECT_STATUS.md) · [Roadmap](docs/ROADMAP.md) ·
[Development guide](docs/DEVELOPMENT.md) · [Contributing](CONTRIBUTING.md) ·
[Security](SECURITY.md)

## Purpose

Provide a reproducible environment for investigating cooling faults before
access to physical control equipment. Operators can generate a scenario,
inspect its telemetry, examine the evidence behind diagnostic hypotheses,
record investigation progress, and replay a stored analysis.

The prototype is not validated for production control. Physical PLC access is
planned from February 2027, subject to access and integration approval. No
company telemetry or real equipment credentials are included.

## Implemented capabilities

- **Synthetic telemetry:** eleven reference scenarios and a dynamic mode with
  workload variation, ambient conditions, fan response and sensor lag.
- **Evidence-based diagnosis:** data-quality checks, signal analysis, fault
  hypotheses, historical matching, hypothesis criticism and source verification.
- **Controlled execution:** 36 registered specialist roles, 12 implemented
  deterministic roles, conditional routing and bounded execution budgets.
- **Persistent investigations:** SQLite records, event lifecycle, audit history,
  optimistic revision checks and reproducible replay of stored inputs.
- **Local API:** validated request/response contracts, separate read/write
  credentials and loopback-only serving by default.
- **Investigation panel:** overview, incidents, telemetry charts, evidence,
  execution traces and scenario configuration in a self-hosted React interface.
- **Reproducible evaluation:** a versioned, seed-disjoint synthetic manifest and
  offline comparison of a threshold baseline, `core6` and `mvp12`.
- **External data intake boundary:** offline CSV provenance, checksum, channel
  units, timestamp and train/validation/test isolation validation. A bounded,
  explicitly marked exploratory review can use a validated CSV window.

Registered roles are not equivalent to active implementations. The remaining
24 roles are planned. Document retrieval currently uses keyword matching over
local demo notes; semantic RAG, learned anomaly models and LLM orchestration are
not implemented. What-if comparisons use an illustrative reduced model, not a
calibrated facility model. See the [capability inventory](docs/PROJECT_STATUS.md).

## Architecture

```mermaid
flowchart LR
    Input[Scenario generator / validated input] --> Contracts[Pydantic contracts]
    Contracts --> Supervisor[Global supervisor]
    Supervisor --> Tools[Deterministic specialists]
    Tools --> Evidence[Evidence verification]
    Evidence --> Report[Diagnostic report]
    Report --> Store[SQLite history and audit]
    Store --> API[Local FastAPI service]
    API --> Panel[React investigation panel]
```

This is a modular Python monorepo with a TypeScript frontend. Specialist roles
share explicit contracts and allowlisted tools. There is no physical actuator
command path. The repository intentionally starts with local execution and
locked dependencies instead of requiring external infrastructure.

## Quick start

Prerequisites: Python **3.12+** and [uv](https://docs.astral.sh/uv/).
Node.js **22.22.2+ on the 22.x line** is the CI target for frontend development; Node is not required
to serve the included panel. Commands below assume macOS/Linux and the
repository root.

```sh
uv sync --locked --extra dev --no-editable
.venv/bin/canovatwin --scenario fan_loss
.venv/bin/canovatwin-api init
.venv/bin/canovatwin-api
```

Open **http://127.0.0.1:8000/panel/**. The initialization command creates
read/write credentials in `.local/api-config.json` with restricted file
permissions. Use a local credential in the panel; never commit or share this
file. Credentials stay in browser memory and clear on reload/logout.

The initial dependency installation requires internet access. Tests and
synthetic demonstrations run offline after installation. No API subscription,
Docker, PostgreSQL or local language model is required.

After editing Python code, refresh the installed CLI/package:

```sh
uv sync --locked --extra dev --no-editable --reinstall-package canovatwin-x
```

Detailed commands: [usage](docs/USAGE.md), [API](docs/API.md),
[history and replay](docs/HISTORY.md), [panel](docs/PANEL.md).

## Development and verification

```sh
npm ci --prefix web
.venv/bin/python scripts/check.py --panel
.venv/bin/python scripts/smoke_api.py
```

The quality gate runs Ruff, pytest with branch coverage, frontend formatting,
TypeScript checks, component/workflow tests and a production build. The HTTP
smoke test exercises a temporary local server and removes its temporary data.

When changing API contracts, regenerate and review frontend types:

```sh
npm run types --prefix web
```

The GitHub workflow targets Python 3.12, 3.13 and 3.14 on Linux. It also builds a
wheel, verifies its panel assets and exercises the installed wheel over HTTP.
A configured workflow is not a successful CI run: inspect the actual checks
on each pull request. Local test evidence is recorded in the
[sprint reports](docs/SPRINT_12_REPORT.md) and
[repository handoff report](docs/GITHUB_HANDOFF_REPORT.md).

## Reproducible experiments

Compare a simple threshold baseline, `core6` and `mvp12` on the same synthetic
telemetry, using seed-disjoint development, validation and test sets:

```sh
.venv/bin/canovatwin-evaluate run examples/evaluation/synthetic-v1.json --split test --output-dir .local/evaluation/run-001
```

The bundled manifest defines 66 cases across three splits; selecting `test`
evaluates 22 cases with three methods. Each run exports its manifest, per-case
CSV, complete JSON results and a readable Markdown summary. Existing run
folders are never overwritten. Fault onset, severity, noise and missing-sensor
fraction can be varied without changing the original dynamic generator.

This provides a reproducible **synthetic benchmark**, not independent field
validation or a trained model. Read [the evaluation protocol](docs/EVALUATION.md)
for denominators, abstentions, data isolation, limitations and interpretation.

## External dataset intake

`canovatwin-dataset` validates a declared external CSV manifest without a
network request. It checks source file hashes, explicit units, timestamp order,
quality counts and asset/time separation across splits:

```sh
.venv/bin/canovatwin-dataset path/to/manifest.json --output .local/dataset-intake.json
```

Source URL and license are **declarations to review**, not independently
verified claims. No external dataset or company data is bundled. See the
[intake contract](docs/DATASET_INTAKE.md) before using a third-party dataset.

After intake, a bounded, read-only exploratory review can run on a named CSV
partition. Missing channels remain missing, labels remain unknown, and even a
`clear` result requires human review:

```sh
.venv/bin/canovatwin-dataset path/to/manifest.json --review-partition site_c_test --offset 0 --count 120 --output .local/external-review.json
```

The normal HTTP analysis endpoint refuses direct external-source claims;
external review goes through the complete manifest and CSV checks.

The [AAU server-room case study](docs/AAU_CASE_STUDY.md) uses two small,
publisher-pinned public CSVs with explicit timezone assumptions. It runs the
full intake and exploratory review path on real measurements without bundling
the third-party data or claiming a fault-diagnosis score.


The separate, read-only Figshare hospital AHU audit checks the publisher's
exact v3 file against its checksum and the paper's reported counts. It does
not run diagnostics or report model accuracy:

```sh
.venv/bin/canovatwin-hospital-audit /path/to/hosptial_scientific_data.csv --output .local/hospital-audit.json
```

See the [source audit and observed discrepancies](docs/FIGSHARE_HOSPITAL_AUDIT.md).

## Offline telemetry stream

`StreamCollector` provides a bounded, in-memory event-time ordering contract
for synthetic telemetry. It explicitly rejects late or duplicate measurements,
clock errors and a full pending buffer; connection and freshness are separate
states. Only committed samples can form an analysis window. See the
[stream contract](docs/STREAM.md). This is not a live device gateway.

For recoverable local replay, `StreamJournal` stores each accepted stream event
in a separate SQLite database. Reopening verifies the event chain and rebuilds
the pending buffer, committed window, watermark and connection state. Writes
are transactional and concurrent handles cannot silently overwrite one another.
See the [journal contract](docs/JOURNAL.md).

## Repository layout

```text
src/canovatwin/       Domain contracts, specialists, simulation and supervisor
  analysis/          Deterministic analysis and evidence tools
  persistence/       SQLite repository and record integrity
  api/               Local HTTP boundary and configuration
  web/               Packaged production panel assets
web/src/             React and TypeScript source
web/tests/           Frontend component and workflow tests
tests/               Python unit, integration and end-to-end tests
scripts/             Quality gate, OpenAPI export and package/HTTP checks
docs/                Design decisions, usage, sprint reports and roadmap
.github/             CI, dependency update configuration and review templates
```

## Research roadmap

The next priorities are independent evaluation, more realistic simulation,
continuous telemetry, a virtual controller test environment and a fuller
operator workspace. Semantic retrieval and further specialist activation follow
measurable evaluation needs. Physical integration remains a later, separately
validated stage. The [roadmap](docs/ROADMAP.md) distinguishes these gaps from
features that already work.

Software test coverage is not a diagnostic accuracy score. Current scenarios
are generated by the same project that implements the diagnostic rules;
independent labeled datasets and architecture comparisons are still required.

## Collaboration and distribution

Use a feature branch, a focused pull request and review by the other developer.
Contributors authenticate with their own accounts; credentials and authorship
are never shared. Read [CONTRIBUTING.md](CONTRIBUTING.md) before pushing changes.

This repository is public and released under the [MIT License](LICENSE).
Third-party packages retain their respective licenses. Company telemetry,
device configurations and confidential documents must never be committed here.
See the [Code of Conduct](CODE_OF_CONDUCT.md) and [Changelog](CHANGELOG.md).
