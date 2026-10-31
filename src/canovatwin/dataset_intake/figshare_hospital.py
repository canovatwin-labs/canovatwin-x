"""Read-only audit of the publisher-pinned hospital AHU CSV, without diagnosis."""

import csv
import hashlib
import io
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

from pydantic import Field

from ..contracts import Contract

SOURCE = "https://doi.org/10.6084/m9.figshare.27147678.v3"
ARTICLE = "https://doi.org/10.1038/s41597-025-05825-9"
FILE_NAME = "hosptial_scientific_data.csv"  # Publisher spelling is intentional.
PUBLISHER_MD5 = "3be98fc565727053878c205de03ffb4f"
MAX_BYTES = 10_000_000
MAX_ROWS = 100_000
PUBLISHED_ROWS = 66_048  # Paper Table 6: actual hospital rows, after missing entries.
PUBLISHED_YEAR = 2022  # Paper Table 5: stated hospital collection year.
PUBLISHED_LABELS = {  # Paper Table 8: hospital column.
    "Normal condition": 53_757,
    "Return air temperature fault": 8_835,
    "Supply air temperature fault": 9,
    "Supply fan fault": 1_921,
    "Valve position fault": 1_525,
    "Cooling supply temperature fault": 1,
}
HEADER = (
    "AHU name",
    "DATE",
    "Time",
    "Set point temperature",
    "Return temperature",
    "Supply air temperature",
    "Supply fan",
    "Valve position",
    "Heat Exchanger",
    "Heating supply temperature",
    "Cooling supply temperature",
    "cooling pump",
    "labeling",
)


class AssetSummary(Contract):
    rows: int = Field(ge=1)
    unique_hours: int = Field(ge=1)
    duplicate_asset_hours: int = Field(ge=0)
    missing_hourly_slots: int = Field(ge=0)
    first_local: datetime
    last_local: datetime


class HospitalAudit(Contract):
    schema_version: Literal["1.0"] = "1.0"
    source_url: str = SOURCE
    article_url: str = ARTICLE
    license_identifier: Literal["CC-BY-4.0"] = "CC-BY-4.0"
    file_name: str = FILE_NAME
    publisher_md5: str = PUBLISHER_MD5
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    rows: int = Field(ge=1)
    first_local: datetime
    last_local: datetime
    years: dict[int, int]
    labels: dict[str, int]
    missing_by_column: dict[str, int]
    assets: dict[str, AssetSummary]
    published_rows: int = PUBLISHED_ROWS
    published_year: int = PUBLISHED_YEAR
    row_count_matches_paper: bool
    year_matches_paper: bool
    label_counts_match_paper: bool
    duplicate_asset_hours: int = Field(ge=0)
    evaluation_status: Literal["source_audit_only"] = "source_audit_only"
    findings: tuple[str, ...]


def _audit(path: Path, *, expected_md5: str) -> HospitalAudit:
    if path.is_symlink() or not path.is_file():
        raise ValueError("Publisher CSV is missing or is a symlink")
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Publisher CSV exceeds 10 MB")
    if hashlib.md5(raw, usedforsecurity=False).hexdigest() != expected_md5:
        raise ValueError("Publisher MD5 mismatch; refusing an unpinned file")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
        if tuple(reader.fieldnames or ()) != HEADER:
            raise ValueError("Publisher CSV header changed")
        years: Counter[int] = Counter()
        labels: Counter[str] = Counter()
        missing: Counter[str] = Counter()
        hours: dict[str, set[datetime]] = defaultdict(set)
        asset_rows: Counter[str] = Counter()
        duplicates: Counter[str] = Counter()
        for number, row in enumerate(reader, start=2):
            if number > MAX_ROWS + 1:
                raise ValueError("Publisher CSV exceeds 100000 data rows")
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Row {number}: CSV column count changed")
            asset = row["AHU name"].strip()
            label = row["labeling"].strip()
            if not asset or not label:
                raise ValueError(f"Row {number}: asset or label is blank")
            try:
                stamp = datetime.strptime(row["DATE"] + " " + row["Time"], "%d/%m/%Y %H:%M")
            except ValueError:
                raise ValueError(f"Row {number}: invalid local date/time") from None
            if stamp.minute or stamp.second:
                raise ValueError(f"Row {number}: timestamp is not on an hourly boundary")
            years[stamp.year] += 1
            labels[label] += 1
            asset_rows[asset] += 1
            if stamp in hours[asset]:
                duplicates[asset] += 1
            hours[asset].add(stamp)
            missing.update(name for name in HEADER if not row[name].strip())
    except (UnicodeError, csv.Error) as exc:
        raise ValueError(f"Invalid publisher CSV: {exc}") from None
    if not asset_rows:
        raise ValueError("Publisher CSV is empty")
    assets = {}
    for asset, stamps in sorted(hours.items()):
        first, last = min(stamps), max(stamps)
        expected_hours = (last - first) // timedelta(hours=1) + 1
        assets[asset] = AssetSummary(
            rows=asset_rows[asset],
            unique_hours=len(stamps),
            duplicate_asset_hours=duplicates[asset],
            missing_hourly_slots=expected_hours - len(stamps),
            first_local=first,
            last_local=last,
        )
    observed_years = set(years)
    findings = []
    if sum(asset_rows.values()) != PUBLISHED_ROWS:
        findings.append("row_count_differs_from_paper")
    if observed_years != {PUBLISHED_YEAR}:
        findings.append("collection_year_differs_from_paper")
    if labels != PUBLISHED_LABELS:
        findings.append("label_counts_differ_from_paper")
    if sum(duplicates.values()):
        findings.append("duplicate_asset_hour_keys")
    if sum(item.missing_hourly_slots for item in assets.values()):
        findings.append("missing_hourly_slots")
    if missing:
        findings.append("blank_sensor_cells")
    return HospitalAudit(
        sha256=hashlib.sha256(raw).hexdigest(),
        rows=sum(asset_rows.values()),
        first_local=min(item.first_local for item in assets.values()),
        last_local=max(item.last_local for item in assets.values()),
        years=dict(sorted(years.items())),
        labels=dict(sorted(labels.items())),
        missing_by_column={name: missing[name] for name in HEADER if missing[name]},
        assets=assets,
        row_count_matches_paper=sum(asset_rows.values()) == PUBLISHED_ROWS,
        year_matches_paper=observed_years == {PUBLISHED_YEAR},
        label_counts_match_paper=labels == PUBLISHED_LABELS,
        duplicate_asset_hours=sum(duplicates.values()),
        findings=tuple(findings),
    )


def audit_hospital_csv(path: Path) -> HospitalAudit:
    """Audit the exact Figshare v3 hospital file; never train or score from its labels."""
    if path.name != FILE_NAME:
        raise ValueError(f"Expected publisher filename {FILE_NAME}")
    return _audit(path, expected_md5=PUBLISHER_MD5)
