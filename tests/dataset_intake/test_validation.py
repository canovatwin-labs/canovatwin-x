"""External intake accepts declared data only after structural checks."""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from canovatwin.dataset_intake.cli import main
from canovatwin.dataset_intake.models import Channel, DatasetManifest, Partition
from canovatwin.dataset_intake.validator import validate_dataset


def fixture_manifest(root: Path, *, starts: tuple[int, int, int] = (0, 3600, 7200)) -> DatasetManifest:
    parts = []
    for index, (split, offset) in enumerate(zip(("train", "validation", "test"), starts, strict=True)):
        start = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=offset)
        rows = ["time,inlet_f,humidity_fraction,load_w,cooling_w,flow_m3h"]
        for step in (0, 60, 180):
            time = (start + timedelta(seconds=step)).isoformat()
            rows.append(f"{time},{75.2 + index},0.45,4200,5000,3600")
        content = ("\n".join(rows) + "\n").encode()
        path = f"{split}.csv"
        (root / path).write_bytes(content)
        parts.append(
            Partition(
                partition_id=f"partition-{index}",
                split=split,
                asset_id=f"unit-{index}",
                path=path,
                sha256=hashlib.sha256(content).hexdigest(),
            )
        )
    return DatasetManifest(
        dataset_id="sample-external",
        source_url="https://example.org/declared-source",
        license_identifier="CC-BY-4.0",
        license_note="Human review of license and source is still required.",
        timestamp_column="time",
        expected_interval_s=60.0,
        channels={
            "inlet_c": Channel(column="inlet_f", unit="degF"),
            "humidity_pct": Channel(column="humidity_fraction", unit="fraction"),
            "it_load_kw": Channel(column="load_w", unit="W"),
            "cooling_kw": Channel(column="cooling_w", unit="W"),
            "airflow_m3s": Channel(column="flow_m3h", unit="m3/h"),
        },
        partitions=tuple(parts),
    )


def test_validated_report_records_quality_and_declared_provenance(tmp_path):
    report = validate_dataset(fixture_manifest(tmp_path), tmp_path)
    assert report.provenance_status == "declared_unverified"
    assert report.analysis_status == "not_connected"
    assert report.source_url == "https://example.org/declared-source"
    assert report.license_identifier == "CC-BY-4.0"
    assert len(report.partitions) == 3
    assert {part.rows for part in report.partitions} == {3}
    assert {part.median_interval_s for part in report.partitions} == {90}
    assert {part.max_gap_s for part in report.partitions} == {120}
    assert {part.gap_count for part in report.partitions} == {1}
    assert all(
        all(count == 0 for count in part.out_of_range_by_channel.values()) for part in report.partitions
    )
    assert report == validate_dataset(fixture_manifest(tmp_path), tmp_path)


@pytest.mark.parametrize("channel,unit", [("inlet_c", "kW"), ("bad_field", "degC")])
def test_unknown_channel_or_unit_rejected(tmp_path, channel, unit):
    manifest = fixture_manifest(tmp_path)
    with pytest.raises(ValidationError):
        DatasetManifest.model_validate(
            manifest.model_dump() | {"channels": {channel: {"column": "inlet_f", "unit": unit}}}
        )


def test_duplicate_column_mapping_and_split_requirements(tmp_path):
    manifest = fixture_manifest(tmp_path)
    with pytest.raises(ValidationError, match="exactly one"):
        DatasetManifest.model_validate(
            manifest.model_dump() | {"channels": {"inlet_c": {"column": "time", "unit": "degC"}}}
        )
    with pytest.raises(ValidationError, match="All three"):
        partitions = (*manifest.partitions[:2], manifest.partitions[2].model_copy(update={"split": "train"}))
        DatasetManifest.model_validate(manifest.model_dump() | {"partitions": partitions})


def test_hash_mismatch_and_nonfinite_value_rejected(tmp_path):
    manifest = fixture_manifest(tmp_path)
    path = tmp_path / "train.csv"
    path.write_text(path.read_text().replace("75.2", "NaN"))
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        validate_dataset(manifest, tmp_path)
    content = path.read_bytes()
    replacement = manifest.partitions[0].model_copy(update={"sha256": hashlib.sha256(content).hexdigest()})
    manifest = manifest.model_copy(update={"partitions": (replacement, *manifest.partitions[1:])})
    with pytest.raises(ValueError, match="nonfinite inlet_c"):
        validate_dataset(manifest, tmp_path)


def test_missing_and_out_of_range_are_reported_after_unit_conversion(tmp_path):
    manifest = fixture_manifest(tmp_path)
    path = tmp_path / "train.csv"
    lines = path.read_text().splitlines()
    lines[1] = lines[1].replace(",75.2,0.45,4200,5000,3600", ",,0.45,4200,5000,3600")
    lines[2] = lines[2].replace(",75.2,0.45,4200,5000,3600", ",212,1.01,4200,5000,3600")
    path.write_text("\n".join(lines) + "\n")
    replacement = manifest.partitions[0].model_copy(
        update={"sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    )
    report = validate_dataset(
        manifest.model_copy(update={"partitions": (replacement, *manifest.partitions[1:])}), tmp_path
    )
    assert report.partitions[0].missing_by_channel["inlet_c"] == 1
    assert report.partitions[0].out_of_range_by_channel["inlet_c"] == 1
    assert report.partitions[0].out_of_range_by_channel["humidity_pct"] == 1


def test_timezone_and_row_shape_fail_closed(tmp_path):
    manifest = fixture_manifest(tmp_path)
    path = tmp_path / "train.csv"
    lines = path.read_text().splitlines()
    lines[1] = lines[1].replace("+00:00", "")
    path.write_text("\n".join(lines) + "\n")
    replacement = manifest.partitions[0].model_copy(
        update={"sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    )
    with pytest.raises(ValueError, match="UTC offset"):
        validate_dataset(
            manifest.model_copy(update={"partitions": (replacement, *manifest.partitions[1:])}), tmp_path
        )
    lines[1] += ",unexpected"
    path.write_text("\n".join(lines) + "\n")
    replacement = replacement.model_copy(update={"sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    with pytest.raises(ValueError, match="column count"):
        validate_dataset(
            manifest.model_copy(update={"partitions": (replacement, *manifest.partitions[1:])}), tmp_path
        )


def test_reordered_time_and_duplicate_header_rejected(tmp_path):
    manifest = fixture_manifest(tmp_path)
    path = tmp_path / "train.csv"
    text = path.read_text()
    lines = text.splitlines()
    lines[2] = lines[1]
    path.write_text("\n".join(lines) + "\n")
    replacement = manifest.partitions[0].model_copy(
        update={"sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    )
    with pytest.raises(ValueError, match="not increasing"):
        validate_dataset(
            manifest.model_copy(update={"partitions": (replacement, *manifest.partitions[1:])}), tmp_path
        )
    path.write_text(text.replace("time,inlet_f", "time,time,inlet_f"))
    replacement = replacement.model_copy(update={"sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    with pytest.raises(ValueError, match="header is missing or repeated"):
        validate_dataset(
            manifest.model_copy(update={"partitions": (replacement, *manifest.partitions[1:])}), tmp_path
        )


def test_asset_and_time_split_isolation(tmp_path):
    manifest = fixture_manifest(tmp_path)
    same_asset = tuple(part.model_copy(update={"asset_id": "shared-unit"}) for part in manifest.partitions)
    with pytest.raises(ValueError, match="multiple evaluation splits"):
        validate_dataset(manifest.model_copy(update={"partitions": same_asset}), tmp_path)
    report = validate_dataset(
        manifest.model_copy(update={"partitions": same_asset, "isolation": "time", "embargo_s": 1800}),
        tmp_path,
    )
    assert len(report.partitions) == 3
    with pytest.raises(ValueError, match="unembargoed"):
        validate_dataset(
            manifest.model_copy(update={"partitions": same_asset, "isolation": "time", "embargo_s": 3600}),
            tmp_path,
        )


def test_content_leakage_detected_after_timestamp_and_asset_changes(tmp_path):
    manifest = fixture_manifest(tmp_path)
    test_path = tmp_path / "test.csv"
    rows = test_path.read_text().splitlines()
    rows = [row.replace("77.2", "75.2") for row in rows]
    test_path.write_text("\n".join(rows) + "\n")
    replacement = manifest.partitions[2].model_copy(
        update={"sha256": hashlib.sha256(test_path.read_bytes()).hexdigest()}
    )
    with pytest.raises(ValueError, match="Identical normalized telemetry"):
        validate_dataset(
            manifest.model_copy(update={"partitions": (*manifest.partitions[:2], replacement)}), tmp_path
        )


def test_path_traversal_and_symlink_escape_rejected(tmp_path):
    manifest = fixture_manifest(tmp_path)
    with pytest.raises(ValidationError, match="relative CSV"):
        Partition.model_validate(manifest.partitions[0].model_dump() | {"path": "../train.csv"})
    root = tmp_path / "nested"
    root.mkdir()
    (root / "train.csv").symlink_to(tmp_path / "train.csv")
    for part in manifest.partitions[1:]:
        (root / part.path).write_bytes((tmp_path / part.path).read_bytes())
    with pytest.raises(ValueError, match="escapes"):
        validate_dataset(manifest, root)


def test_cli_export_does_not_overwrite_and_rejects_large_manifest(tmp_path, capsys):
    manifest = fixture_manifest(tmp_path)
    source = tmp_path / "manifest.json"
    source.write_text(manifest.model_dump_json())
    output = tmp_path / "report.json"
    assert main([str(source), "--output", str(output)]) == 0
    result = json.loads(output.read_text())
    assert result["analysis_status"] == "not_connected"
    assert main([str(source), "--output", str(output)]) == 2
    assert "exists" in capsys.readouterr().err
    source.write_text(" " * 1_000_001)
    assert main([str(source)]) == 2
    assert "1 MB" in capsys.readouterr().err
