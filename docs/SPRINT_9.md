# Sprint 9 — Declared external telemetry exploratory review

Goal: connect the Sprint 8 validated CSV boundary to a bounded, read-only
analysis without presenting unlicensed or unlabeled data as field validation.

Acceptance:

1. Validate all manifest partitions before selecting 3–600 CSV rows; recheck
   the selected file hash immediately before creating an analysis window.
2. Convert mapped channels to canonical units and leave absent channels `null`.
   Missing fields must lead to the existing quality abstention when appropriate.
3. Mark input, evidence and run as `declared_external`/`external_review`; label
   status remains unknown. `clear` never removes mandatory human review.
4. Keep source URL, license declaration, manifest/file hashes, row selection
   and input hash in the review report. No raw CSV is stored in history.
5. Direct external-source claims on the HTTP analysis route return 422 because
   they bypass the intake checks. Synthetic inputs and replay retain behavior.
6. Offline CLI, targeted tests, installed-wheel smoke, full Python/panel gate
   and Linux CI verify the path.

Deferred: verified real publisher license, sensor semantics, actual independent
dataset, ground-truth fault labels, field performance metrics, real PLC access.
