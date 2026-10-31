"""Reproducible, offline AAU server-room case study; no inferred fault labels."""

import csv
import hashlib
import io
import json
import re
from datetime import datetime, timedelta, timezone
from math import isfinite
from pathlib import Path
from tempfile import TemporaryDirectory

from .models import Channel, DatasetManifest, Partition
from .review import review_partition
from .validator import validate_dataset

SOURCE = "https://zenodo.org/records/21262042"
DOI = "10.5281/zenodo.21262042"
FILES = {
    "ventilation": ("AAU_supplementary_ventilation.csv", "e263cb768ccad12f50e4de1ada9e610b"),
    "surroundings": (
        "AAU_supplementary_surrounding_temperatures.csv",
        "3c8ca0ff02e4dc3ea40d40a5200774da",
    ),
}
MAX_SOURCE_BYTES = 1_000_000
OFFSET = re.compile(r"^([+-])(0\d|1[0-4]):([0-5]\d)$")


def _offset(value: str) -> timezone:
    match = OFFSET.fullmatch(value)
    if match is None:
        raise ValueError("source_offset must be an explicit ±HH:MM offset")
    hours, minutes = int(match[2]), int(match[3])
    if hours == 14 and minutes:
        raise ValueError("UTC offset cannot exceed 14 hours")
    duration = timedelta(hours=hours, minutes=minutes)
    return timezone(duration if match[1] == "+" else -duration)


def _rows(path: Path, expected_md5: str, column: str) -> tuple[dict[datetime, str], str]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Missing or linked publisher file: {path.name}")
    with path.open("rb") as stream:
        raw = stream.read(MAX_SOURCE_BYTES + 1)
    if len(raw) > MAX_SOURCE_BYTES:
        raise ValueError(f"Publisher file exceeds the bounded reader: {path.name}")
    published = hashlib.md5(raw, usedforsecurity=False).hexdigest()
    if published != expected_md5:
        raise ValueError(f"Publisher MD5 does not match: {path.name}")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
        header = reader.fieldnames
        if header is None or len(header) != len(set(header)) or not {"time", column} <= set(header):
            raise ValueError(f"Publisher CSV header changed: {path.name}")
        observed = {}
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Publisher CSV row shape changed: {path.name}")
            value = row[column].strip()
            if not value:
                continue
            timestamp = datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S")
            if timestamp in observed:
                raise ValueError(f"Duplicate publisher timestamp: {path.name}")
            # Reject malformed, NaN and infinite readings before canonical intake.
            if not isfinite(float(value)):
                raise ValueError(f"Nonfinite publisher reading: {path.name}")
            observed[timestamp] = value
    except (UnicodeError, csv.Error) as exc:
        raise ValueError(f"Invalid publisher CSV: {path.name}") from exc
    return observed, hashlib.sha256(raw).hexdigest()


def _prepare(
    source_dir: Path,
    output_dir: Path,
    *,
    source_offset: str,
    checksums: dict[str, tuple[str, str]],
) -> dict:
    zone = _offset(source_offset)
    if output_dir.exists():
        raise ValueError("Output directory already exists")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    ventilation, vent_sha = _rows(
        source_dir / checksums["ventilation"][0],
        checksums["ventilation"][1],
        "AHU_temperature_supply",
    )
    surroundings, surroundings_sha = _rows(
        source_dir / checksums["surroundings"][0],
        checksums["surroundings"][1],
        "Outdoor_temperature",
    )
    common = sorted(ventilation.keys() & surroundings.keys())
    if len(common) < 30:
        raise ValueError("Fewer than 30 exact, measured timestamp matches")
    # One hour embargo: skip five 15-minute observations at each boundary.
    usable = len(common) - 10
    partition_size = usable // 3
    if partition_size < 3:
        raise ValueError("Not enough observations after time embargo")
    groups = (
        common[:partition_size],
        common[partition_size + 5 : 2 * partition_size + 5],
        common[2 * partition_size + 10 :],
    )
    with TemporaryDirectory(prefix="aau-", dir=output_dir.parent) as temporary:
        root = Path(temporary)
        partitions = []
        for split, times in zip(("train", "validation", "test"), groups, strict=True):
            name = f"{split}.csv"
            with (root / name).open("w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(("timestamp", "supply_c", "ambient_c"))
                for timestamp in times:
                    writer.writerow(
                        (
                            timestamp.replace(tzinfo=zone).isoformat(),
                            ventilation[timestamp],
                            surroundings[timestamp],
                        )
                    )
            partitions.append(
                Partition(
                    partition_id=f"aau_{split}",
                    split=split,
                    asset_id="aau-serverroom",
                    path=name,
                    sha256=hashlib.sha256((root / name).read_bytes()).hexdigest(),
                )
            )
        manifest = DatasetManifest(
            dataset_id="aau-serverroom-v5-supplementary",
            source_url=SOURCE,
            license_identifier="CC-BY-4.0",
            license_note=(
                "AAU Zenodo v5 DOI 10.5281/zenodo.21262042; attribution required. "
                "Source timestamps omit timezone; supplied fixed offset is an unverified assumption. "
                "Temperature columns are interpreted as degC for exploratory review."
            ),
            isolation="time",
            embargo_s=3600,
            timestamp_column="timestamp",
            expected_interval_s=900,
            channels={
                "supply_c": Channel(column="supply_c", unit="degC"),
                "ambient_c": Channel(column="ambient_c", unit="degC"),
            },
            partitions=tuple(partitions),
        )
        (root / "manifest.json").write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
        intake = validate_dataset(manifest, root)
        review = review_partition(manifest, root, "aau_test", count=min(120, len(groups[2])))
        report = {
            "source_url": SOURCE,
            "doi": DOI,
            "license": "CC-BY-4.0",
            "source_offset_assumption": source_offset,
            "raw_sha256": {"ventilation": vent_sha, "surroundings": surroundings_sha},
            "exact_matches": len(common),
            "excluded_by_embargo": 10,
            "intake": intake.model_dump(mode="json"),
            "review": review.model_dump(mode="json"),
            "interpretation": "Unlabeled two-channel exploratory quality review; no fault accuracy claim.",
        }
        (root / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        root.rename(output_dir)
    return report


def prepare_aau(source_dir: Path, output_dir: Path, *, source_offset: str) -> dict:
    """Use publisher-pinned v5 files; no network request or checksum override."""
    return _prepare(source_dir, output_dir, source_offset=source_offset, checksums=FILES)
