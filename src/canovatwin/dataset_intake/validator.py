"""Bounded CSV validation, unit normalization and split leakage checks."""

import csv
import hashlib
import io
import json
from datetime import datetime
from math import isfinite
from pathlib import Path
from statistics import median

from ..analysis.quality import BOUNDS
from .models import DatasetManifest, IntakeReport, Partition, PartitionSummary

MAX_BYTES = 10_000_000
MAX_ROWS = 100_000


def _convert(value: float, unit: str) -> float:
    if unit == "degF":
        return (value - 32) * 5 / 9
    if unit == "K":
        return value - 273.15
    if unit == "fraction":
        return value * 100
    if unit == "m3/h":
        return value / 3600
    if unit == "W":
        return value / 1000
    return value


def _timestamp(value: str, partition_id: str, row: int) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"{partition_id} row {row}: invalid ISO 8601 timestamp") from None
    if result.utcoffset() is None:
        raise ValueError(f"{partition_id} row {row}: timestamp needs a UTC offset")
    return result


def _read_partition(root: Path, manifest: DatasetManifest, part: Partition) -> PartitionSummary:
    path = (root / part.path).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"{part.partition_id}: CSV path escapes the manifest directory or is missing")
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError(f"{part.partition_id}: CSV exceeds 10 MB")
    actual_hash = hashlib.sha256(data).hexdigest()
    if actual_hash != part.sha256:
        raise ValueError(f"{part.partition_id}: CSV SHA-256 mismatch")
    try:
        reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline=""), strict=True)
        header = reader.fieldnames
        if header is None or len(header) != len(set(header)):
            raise ValueError("CSV header is missing or repeated")
        needed = {manifest.timestamp_column, *(channel.column for channel in manifest.channels.values())}
        if not needed.issubset(header):
            raise ValueError("CSV is missing a mapped column")
        timestamps = []
        missing = dict.fromkeys(manifest.channels, 0)
        invalid = dict.fromkeys(manifest.channels, 0)
        gaps = []
        content_hash = hashlib.sha256()
        for row_number, record in enumerate(reader, start=2):
            if row_number > MAX_ROWS + 1:
                raise ValueError("CSV exceeds 100000 data rows")
            if None in record or any(value is None for value in record.values()):
                raise ValueError(f"row {row_number}: inconsistent CSV column count")
            current = _timestamp(record[manifest.timestamp_column], part.partition_id, row_number)
            if timestamps:
                gap = (current - timestamps[-1]).total_seconds()
                if gap <= 0:
                    raise ValueError(f"{part.partition_id} row {row_number}: timestamps are not increasing")
                gaps.append(gap)
            timestamps.append(current)
            normalized_row = {}
            for name, channel in manifest.channels.items():
                raw = record[channel.column].strip()
                if not raw:
                    missing[name] += 1
                    normalized_row[name] = None
                    continue
                try:
                    value = float(raw)
                except ValueError:
                    raise ValueError(f"{part.partition_id} row {row_number}: nonnumeric {name}") from None
                if not isfinite(value):
                    raise ValueError(f"{part.partition_id} row {row_number}: nonfinite {name}")
                normalized = _convert(value, channel.unit)
                normalized_row[name] = round(normalized, 6) if normalized else 0.0
                low, high = BOUNDS[name]
                invalid[name] += not low <= normalized <= high
            content_hash.update(
                json.dumps(normalized_row, sort_keys=True, separators=(",", ":")).encode() + b"\n"
            )
    except (UnicodeError, csv.Error) as exc:
        raise ValueError(f"{part.partition_id}: invalid UTF-8 or CSV: {exc}") from None
    if len(timestamps) < 3:
        raise ValueError(f"{part.partition_id}: at least three rows are required")
    return PartitionSummary(
        partition_id=part.partition_id,
        split=part.split,
        asset_id=part.asset_id,
        sha256=actual_hash,
        content_fingerprint=content_hash.hexdigest(),
        rows=len(timestamps),
        first=timestamps[0],
        last=timestamps[-1],
        median_interval_s=median(gaps),
        max_gap_s=max(gaps),
        missing_by_channel=missing,
        out_of_range_by_channel=invalid,
        gap_count=sum(gap > manifest.expected_interval_s * 1.5 for gap in gaps),
    )


def validate_dataset(manifest: DatasetManifest, root: Path) -> IntakeReport:
    manifest = DatasetManifest.model_validate(manifest.model_dump())
    summaries = tuple(_read_partition(root, manifest, part) for part in manifest.partitions)
    fingerprints: dict[str, str] = {}
    for part in summaries:
        prior_split = fingerprints.get(part.content_fingerprint)
        if prior_split is not None and prior_split != part.split:
            raise ValueError("Identical normalized telemetry content occurs in multiple evaluation splits")
        fingerprints[part.content_fingerprint] = part.split
    for index, left in enumerate(summaries):
        for right in summaries[index + 1 :]:
            if left.asset_id != right.asset_id or left.split == right.split:
                continue
            if manifest.isolation == "asset":
                raise ValueError(f"Asset {left.asset_id} occurs in multiple evaluation splits")
            separated = (right.first - left.last).total_seconds() > manifest.embargo_s or (
                left.first - right.last
            ).total_seconds() > manifest.embargo_s
            if not separated:
                raise ValueError(f"Asset {left.asset_id} has overlapping or unembargoed split intervals")
    digest = hashlib.sha256(
        json.dumps(manifest.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return IntakeReport(
        dataset_id=manifest.dataset_id,
        manifest_sha256=digest,
        source_url=manifest.source_url,
        license_identifier=manifest.license_identifier,
        license_note=manifest.license_note,
        isolation=manifest.isolation,
        embargo_s=manifest.embargo_s,
        partitions=summaries,
    )
