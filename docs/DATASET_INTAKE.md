# External telemetry intake contract

The offline `canovatwin-dataset` command validates **declared** third-party CSV
telemetry before any analysis. It neither downloads data nor sends it to the
supervisor. A source URL, license identifier and review note are required, but
the program does not verify the URL, license rights or physical sensor meaning.
A human must check those against the publisher's terms and schema.

## Manifest

Place a JSON manifest beside its CSV files. Its `partitions` must contain at
least one `train`, `validation` and `test` file. Every file has a distinct ID,
relative CSV path, asset ID and SHA-256. `path` cannot escape the manifest
directory, including through a symbolic link. The `source_url` must be HTTPS.

```json
{
  "schema_version": "1.0",
  "dataset_id": "publisher_dataset_v1",
  "source_url": "https://publisher.example/dataset",
  "license_identifier": "CC-BY-4.0",
  "license_note": "Review the publisher's current license and attribution conditions before use.",
  "isolation": "asset",
  "embargo_s": 3600,
  "timestamp_column": "timestamp_utc",
  "expected_interval_s": 60.0,
  "channels": {
    "inlet_c": {"column": "inlet_f", "unit": "degF"},
    "it_load_kw": {"column": "it_power_w", "unit": "W"}
  },
  "partitions": [
    {"partition_id": "site_a_train", "split": "train", "asset_id": "site_a", "path": "train.csv", "sha256": "REPLACE_WITH_FILE_SHA256"},
    {"partition_id": "site_b_validation", "split": "validation", "asset_id": "site_b", "path": "validation.csv", "sha256": "REPLACE_WITH_FILE_SHA256"},
    {"partition_id": "site_c_test", "split": "test", "asset_id": "site_c", "path": "test.csv", "sha256": "REPLACE_WITH_FILE_SHA256"}
  ]
}
```

The example describes the shape; replace URLs, license claims, paths and hashes
with reviewed values. Compute each file's hash with `shasum -a 256 FILE` on
macOS or `sha256sum FILE` on Linux. These commands do not prove source identity;
compare the downloaded file with the publisher's own checksum when available.

## Supported units

- Temperatures (`inlet_c`, `reference_inlet_c`, `return_c`, `supply_c`,
  `ambient_c`): `degC`, `degF`, `K`; normalized to °C.
- Humidity and fan command/feedback: `pct` or `fraction`; normalized to %.
- Airflow: `m3/s` or `m3/h`; normalized to m³/s.
- IT load and cooling capacity: `kW` or `W`; normalized to kW.

Mapped CSV headers must be unique. Blank cells count as missing; nonnumeric or
nonfinite values fail validation. Values outside the current illustrative
quality ranges are counted, not silently clipped. `cooling_kw` is thermal
cooling capacity, **not electrical power**. Do not map a chiller electricity
column to it. The validator cannot infer a column's physical meaning.

Timestamps must be ISO 8601 with a UTC offset and strictly increase in each
file. Gaps greater than 1.5 times `expected_interval_s` are counted. A report
contains row count, first/last time, median interval, maximum gap, missing and
out-of-range counts. CSV input is limited to 10 MB and 100,000 rows per file;
the manifest to 1 MB and 100 partitions. Reports never overwrite an existing
file. No CSV measurements are exported in the report.

`isolation="asset"` rejects any asset shared across splits. For a longitudinal
study, `isolation="time"` permits the same asset only when split intervals are
separated by **more than** `embargo_s`. Exact normalized sensor sequences copied
across splits are rejected at 0.000001-unit precision even if timestamps and
asset IDs change. These are
leakage guards, not proof that two data sources are statistically independent.

## Exploratory review after validation

The ordinary intake report deliberately says
`provenance_status=declared_unverified` and `analysis_status=not_connected`.
The separate review option validates **all** partitions, then reads a bounded
3–600-row window from the named partition and rechecks its file hash. It maps
declared channels to canonical units; unmapped channels remain `null`. The
existing deterministic `core6` rules run on a `declared_external` window:

```sh
.venv/bin/canovatwin-dataset manifest.json --review-partition site_c_test --offset 0 --count 120 --output review.json
```

The review report records dataset/partition/file hashes, declared source and
license, row selection, input hash, unknown label status and the complete
analysis trace. Evidence carries the `declared_external` source. The run mode
is `external_review`, and `human_review_required` stays true even if the
example rules return `clear`. The CLI does not save the run to investigation
history. The ordinary HTTP analysis endpoint refuses a direct external-source
claim because it would bypass the manifest checks.

No external dataset is bundled, no real-data accuracy is reported, and source
rights or physical sensor semantics are not verified by this code. Missing
channels commonly lead to `insufficient_data`; they are not imputed. A real
dataset still needs publisher documentation, license review, unit/tag mapping
and human interpretation before any conclusion is cited.
