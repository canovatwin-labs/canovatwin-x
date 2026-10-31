"""Offline publisher adapter regression without downloading third-party data in CI."""

import csv
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from canovatwin.dataset_intake.aau import _prepare, prepare_aau


def fixture_files(root: Path, *, count: int = 50, shifted: bool = False):
    root.mkdir()
    start = datetime(2024, 9, 16, 16, 45)
    vent = root / "vent.csv"
    surroundings = root / "surroundings.csv"
    with vent.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("time", "AHU_temperature_supply"))
        for index in range(count):
            writer.writerow(
                ((start + timedelta(minutes=15 * index)).strftime("%Y-%m-%d %H:%M:%S"), 17 + index / 100)
            )
    with surroundings.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("time", "Outdoor_temperature"))
        for index in range(count):
            minutes = 15 * index + (1 if shifted else 0)
            writer.writerow(
                ((start + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S"), 12 + index / 100)
            )
    checksums = {
        "ventilation": (vent.name, hashlib.md5(vent.read_bytes(), usedforsecurity=False).hexdigest()),
        "surroundings": (
            surroundings.name,
            hashlib.md5(surroundings.read_bytes(), usedforsecurity=False).hexdigest(),
        ),
    }
    return checksums


def test_exact_join_split_embargo_and_exploratory_review(tmp_path):
    source = tmp_path / "source"
    checksums = fixture_files(source)
    output = tmp_path / "derived"
    report = _prepare(source, output, source_offset="+02:00", checksums=checksums)
    assert report["exact_matches"] == 50
    assert report["excluded_by_embargo"] == 10
    assert sum(part["rows"] for part in report["intake"]["partitions"]) == 40
    assert report["review"]["label_status"] == "unknown"
    assert report["review"]["run"]["report"]["human_review_required"] is True
    assert report["review"]["run"]["report"]["status"] == "insufficient_data"
    assert (output / "manifest.json").is_file()
    assert (output / "report.json").is_file()
    with (output / "train.csv").open() as stream:
        first = next(csv.DictReader(stream))
    assert first["timestamp"].endswith("+02:00")
    assert set(first) == {"timestamp", "supply_c", "ambient_c"}


@pytest.mark.parametrize("offset", ["", "Europe/Copenhagen", "+15:00", "+14:01", "02:00"])
def test_offset_must_be_explicit_fixed_utc_offset(tmp_path, offset):
    with pytest.raises(ValueError, match="offset"):
        _prepare(tmp_path, tmp_path / "derived", source_offset=offset, checksums={})


def test_raw_checksum_mismatch_rejects_without_output(tmp_path):
    source = tmp_path / "source"
    checksums = fixture_files(source)
    checksums["ventilation"] = ("vent.csv", "0" * 32)
    output = tmp_path / "derived"
    with pytest.raises(ValueError, match="MD5"):
        _prepare(source, output, source_offset="+02:00", checksums=checksums)
    assert not output.exists()


def test_no_interpolation_when_timestamps_do_not_match(tmp_path):
    source = tmp_path / "source"
    checksums = fixture_files(source, shifted=True)
    with pytest.raises(ValueError, match="exact"):
        _prepare(source, tmp_path / "derived", source_offset="+02:00", checksums=checksums)


def test_existing_output_and_wrong_publisher_names_are_rejected(tmp_path):
    source = tmp_path / "source"
    checksums = fixture_files(source)
    output = tmp_path / "derived"
    output.mkdir()
    with pytest.raises(ValueError, match="already exists"):
        _prepare(source, output, source_offset="+02:00", checksums=checksums)
    with pytest.raises(ValueError, match="Missing"):
        prepare_aau(source, tmp_path / "publisher", source_offset="+02:00")
