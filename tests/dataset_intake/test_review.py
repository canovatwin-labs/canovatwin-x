"""External review keeps provenance visible and never fabricates missing data."""

import hashlib
import json
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from canovatwin.api.models import AnalyzeBody
from canovatwin.contracts import AnalysisRequest
from canovatwin.dataset_intake.cli import main
from canovatwin.dataset_intake.models import CHANNEL_UNITS, Channel, DatasetManifest, Partition
from canovatwin.dataset_intake.review import review_partition
from canovatwin.telemetry import Scenario, generate_case

from .test_validation import fixture_manifest


def test_review_with_missing_channels_abstains_and_marks_external(tmp_path):
    manifest = fixture_manifest(tmp_path)
    review = review_partition(manifest, tmp_path, "partition-2", count=3)
    assert review.provenance_status == "declared_unverified"
    assert review.label_status == "unknown"
    assert "Human review" in review.license_note
    assert review.run.mode == "external_review"
    assert review.run.status == "completed"
    assert review.run.report.status == "insufficient_data"
    assert review.run.report.human_review_required
    assert review.run.commands == () and review.run.llm_calls == 0
    assert all(item.source == "declared_external" for item in review.run.evidence)
    assert "yalnız beyan" in review.run.report.limitations[0]


def full_channel_manifest(tmp_path):
    parts = []
    channels = {
        name: Channel(
            column=name,
            unit="degC"
            if name.endswith("_c")
            else "pct"
            if name.endswith("_pct")
            else "m3/s"
            if name == "airflow_m3s"
            else "kW",
        )
        for name in CHANNEL_UNITS
    }
    header = "timestamp," + ",".join(channels)
    for index, split in enumerate(("train", "validation", "test")):
        start = datetime(2026, 1, 1 + index, tzinfo=UTC)
        case = generate_case(Scenario.NORMAL, count=120, seed=42 + index, start=start)
        rows = [header]
        for sample in case.window.samples:
            values = [str(getattr(sample, name)) for name in channels]
            rows.append(sample.timestamp.isoformat() + "," + ",".join(values))
        content = ("\n".join(rows) + "\n").encode()
        path = tmp_path / f"{split}.csv"
        path.write_bytes(content)
        parts.append(
            Partition(
                partition_id=split,
                split=split,
                asset_id=f"unit-{index}",
                path=path.name,
                sha256=hashlib.sha256(content).hexdigest(),
            )
        )
    return DatasetManifest(
        dataset_id="full-channel-fixture",
        source_url="https://example.org/local-fixture",
        license_identifier="MIT",
        license_note="Locally generated test fixture, not an independent dataset.",
        timestamp_column="timestamp",
        expected_interval_s=1,
        channels=channels,
        partitions=tuple(parts),
    )


def test_full_channel_review_still_requires_human_and_preserves_synthetic_results(tmp_path):
    manifest = full_channel_manifest(tmp_path)
    review = review_partition(manifest, tmp_path, "test", count=120)
    assert review.run.mode == "external_review"
    assert review.run.status == "completed"
    assert review.run.report.status == "clear"
    assert review.run.report.human_review_required
    assert all(e.source == "declared_external" for e in review.run.evidence)
    assert review.run.total_tool_calls > 0
    repeated = review_partition(manifest, tmp_path, "test", count=120)
    assert review.input_sha256 == repeated.input_sha256
    assert review.run.report == repeated.run.report
    assert review.run.evidence == repeated.run.evidence


def test_api_boundary_rejects_direct_external_claim(request_factory):
    request = request_factory()
    external = request.model_copy(
        update={"window": request.window.model_copy(update={"source": "declared_external"})}
    )
    AnalysisRequest.model_validate(external.model_dump())
    with pytest.raises(ValidationError, match="offline dataset intake"):
        AnalyzeBody(request=external)


def test_review_rejects_unknown_partition_and_short_window(tmp_path):
    manifest = fixture_manifest(tmp_path)
    with pytest.raises(ValueError, match="Unknown partition"):
        review_partition(manifest, tmp_path, "missing", count=3)
    with pytest.raises(ValueError, match="exceeds"):
        review_partition(manifest, tmp_path, "partition-0", offset=1, count=3)
    with pytest.raises(ValueError, match="between 3 and 600"):
        review_partition(manifest, tmp_path, "partition-0", count=2)


def test_cli_review_exports_nonoverwriting_provenance_bound_report(tmp_path):
    manifest = fixture_manifest(tmp_path)
    source = tmp_path / "manifest.json"
    source.write_text(manifest.model_dump_json())
    output = tmp_path / "review.json"
    assert (
        main([str(source), "--review-partition", "partition-2", "--count", "3", "--output", str(output)]) == 0
    )
    report = json.loads(output.read_text())
    assert report["run"]["mode"] == "external_review"
    assert report["label_status"] == "unknown"
    assert report["file_sha256"] == manifest.partitions[2].sha256
    assert (
        main([str(source), "--review-partition", "partition-2", "--count", "3", "--output", str(output)]) == 2
    )
    assert main([str(source), "--offset", "1"]) == 2
