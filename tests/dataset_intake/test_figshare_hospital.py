"""Synthetic regression tests for the pinned, read-only hospital audit."""

import csv
import hashlib
from pathlib import Path

import pytest

from canovatwin.dataset_intake import figshare_hospital_cli
from canovatwin.dataset_intake.figshare_hospital import HEADER, _audit, audit_hospital_csv
from canovatwin.dataset_intake.figshare_hospital_cli import main


def fixture(path: Path, *, duplicate: bool = False, year: int = 2023) -> str:
    rows = []
    for hour, label in ((0, "Normal condition"), (1, "Supply fan fault"), (3, "Normal condition")):
        row = dict.fromkeys(HEADER, "1")
        row.update({"AHU name": "AHU-N01", "DATE": f"01/01/{year}", "Time": f"{hour:02d}:00"})
        row["labeling"] = label
        row["Return temperature"] = "" if hour == 3 else "21"
        rows.append(row)
    if duplicate:
        rows.append(rows[1].copy())
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(rows)
    return hashlib.md5(path.read_bytes(), usedforsecurity=False).hexdigest()


def test_audit_reports_time_quality_and_source_limitations(tmp_path):
    path = tmp_path / "hosptial_scientific_data.csv"
    checksum = fixture(path, duplicate=True)
    report = _audit(path, expected_md5=checksum)
    assert report.rows == 4
    assert report.years == {2023: 4}
    assert report.labels == {"Normal condition": 2, "Supply fan fault": 2}
    assert report.missing_by_column == {"Return temperature": 1}
    assert report.duplicate_asset_hours == 1
    assert report.assets["AHU-N01"].missing_hourly_slots == 1
    assert report.evaluation_status == "source_audit_only"
    assert report.row_count_matches_paper is False
    assert report.year_matches_paper is False
    assert report.label_counts_match_paper is False
    assert set(report.findings) == {
        "row_count_differs_from_paper",
        "collection_year_differs_from_paper",
        "label_counts_differ_from_paper",
        "duplicate_asset_hour_keys",
        "missing_hourly_slots",
        "blank_sensor_cells",
    }


def test_publisher_pin_rejects_changed_file(tmp_path):
    path = tmp_path / "hosptial_scientific_data.csv"
    fixture(path)
    with pytest.raises(ValueError, match="MD5"):
        audit_hospital_csv(path)
    with pytest.raises(ValueError, match="MD5"):
        _audit(path, expected_md5="0" * 32)


def test_rejects_changed_schema_and_malformed_hour(tmp_path):
    path = tmp_path / "hosptial_scientific_data.csv"
    checksum = fixture(path)
    with path.open("a", encoding="utf-8") as stream:
        stream.write("bad,row\n")
    checksum = hashlib.md5(path.read_bytes(), usedforsecurity=False).hexdigest()
    with pytest.raises(ValueError, match="column count"):
        _audit(path, expected_md5=checksum)
    fixture(path)
    contents = path.read_text().replace("01:00", "01:30")
    path.write_text(contents)
    checksum = hashlib.md5(path.read_bytes(), usedforsecurity=False).hexdigest()
    with pytest.raises(ValueError, match="hourly boundary"):
        _audit(path, expected_md5=checksum)


def test_rejects_symlink_and_changed_header(tmp_path):
    path = tmp_path / "hosptial_scientific_data.csv"
    checksum = fixture(path)
    linked = tmp_path / "linked.csv"
    linked.symlink_to(path)
    with pytest.raises(ValueError, match="symlink"):
        _audit(linked, expected_md5=checksum)
    path.write_text(path.read_text().replace("AHU name", "equipment name", 1))
    checksum = hashlib.md5(path.read_bytes(), usedforsecurity=False).hexdigest()
    with pytest.raises(ValueError, match="header changed"):
        _audit(path, expected_md5=checksum)


def test_cli_rejects_unpinned_input_without_overwriting_output(tmp_path, capsys):
    path = tmp_path / "hosptial_scientific_data.csv"
    fixture(path)
    output = tmp_path / "report.json"
    output.write_text("preserve")
    assert main([str(path), "--output", str(output)]) == 2
    assert output.read_text() == "preserve"
    assert "MD5 mismatch" in capsys.readouterr().err


def test_cli_writes_new_report_once(tmp_path, monkeypatch):
    path = tmp_path / "hosptial_scientific_data.csv"
    checksum = fixture(path)
    monkeypatch.setattr(
        figshare_hospital_cli,
        "audit_hospital_csv",
        lambda source: _audit(source, expected_md5=checksum),
    )
    output = tmp_path / "report.json"
    assert main([str(path), "--output", str(output)]) == 0
    assert '"evaluation_status": "source_audit_only"' in output.read_text()
    before = output.read_bytes()
    assert main([str(path), "--output", str(output)]) == 2
    assert output.read_bytes() == before
