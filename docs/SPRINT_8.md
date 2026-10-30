# Sprint 8 — External telemetry intake foundation

Goal: make the first independent-data step code-reviewable without claiming
that an external dataset has already been licensed or validated.

Acceptance:

1. Strict versioned manifest declares source, license note, canonical column
   mappings, units, sampling interval, file hashes and train/validation/test
   partitions. Declarations remain explicitly unverified.
2. Offline CSV validator has bounded input, rejects path traversal, hash
   mismatch, malformed numeric/time values and non-increasing timestamps.
3. Normalized measurements support field-specific unit conversion and report
   missing, out-of-range and sampling-gap counts without imputation.
4. Asset-disjoint or time-embargoed split rules and duplicate normalized-content
   checks prevent basic leakage.
5. CLI exports a non-overwriting JSON report. No external data is passed to the
   existing synthetic-only supervisor or stored in the repository.
6. Targeted failure tests, full Python/panel gate and installed-wheel smoke
   verify this boundary on supported Python versions.

Explicitly deferred: selecting/downloading a real dataset, license verification,
manufacturer tag mapping, diagnostic evaluation on external data, field
calibration, and real PLC integration.
