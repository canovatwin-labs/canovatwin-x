"""Strict intake contracts; declared provenance is never treated as verified."""

from datetime import datetime
from pathlib import PurePath
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Contract

Split = Literal["train", "validation", "test"]
Isolation = Literal["asset", "time"]
CHANNEL_UNITS: dict[str, tuple[str, ...]] = {
    **{
        name: ("degC", "degF", "K")
        for name in ("inlet_c", "reference_inlet_c", "return_c", "supply_c", "ambient_c")
    },
    **{name: ("pct", "fraction") for name in ("humidity_pct", "fan_command_pct", "fan_feedback_pct")},
    "airflow_m3s": ("m3/s", "m3/h"),
    "it_load_kw": ("kW", "W"),
    "cooling_kw": ("kW", "W"),
}


class Channel(Contract):
    column: str = Field(min_length=1, max_length=100)
    unit: str = Field(min_length=1, max_length=16)


class Partition(Contract):
    partition_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    split: Split
    asset_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,100}$")
    path: str = Field(min_length=1, max_length=200)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def safe_path(self):
        location = PurePath(self.path)
        if location.is_absolute() or ".." in location.parts or location.suffix.lower() != ".csv":
            raise ValueError("Partition path must be a relative CSV path without parent traversal")
        return self


class DatasetManifest(Contract):
    schema_version: Literal["1.0"] = "1.0"
    dataset_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    source_url: str = Field(pattern=r"^https://[^\s]{1,500}$")
    license_identifier: str = Field(pattern=r"^[A-Za-z0-9.+-]{1,80}$")
    license_note: str = Field(min_length=10, max_length=1000)
    isolation: Isolation = "asset"
    embargo_s: int = Field(default=3600, ge=0, le=604800)
    timestamp_column: str = Field(min_length=1, max_length=100)
    expected_interval_s: float = Field(gt=0, le=3600)
    channels: dict[str, Channel] = Field(min_length=1, max_length=11)
    partitions: tuple[Partition, ...] = Field(min_length=3, max_length=100)

    @model_validator(mode="after")
    def consistent_mapping(self):
        if set(self.channels) - set(CHANNEL_UNITS):
            raise ValueError("Unknown canonical channel")
        columns = [channel.column for channel in self.channels.values()]
        if len(set(columns + [self.timestamp_column])) != len(columns) + 1:
            raise ValueError("CSV columns must map to exactly one canonical field")
        for name, channel in self.channels.items():
            if channel.unit not in CHANNEL_UNITS[name]:
                raise ValueError(f"Unsupported unit for {name}: {channel.unit}")
        if {part.split for part in self.partitions} != {"train", "validation", "test"}:
            raise ValueError("All three evaluation splits are required")
        if len({part.partition_id for part in self.partitions}) != len(self.partitions):
            raise ValueError("Partition IDs must be unique")
        if len({part.path for part in self.partitions}) != len(self.partitions):
            raise ValueError("Partition paths must be unique")
        if len({part.sha256 for part in self.partitions}) != len(self.partitions):
            raise ValueError("Duplicate file content across partitions")
        return self


class PartitionSummary(Contract):
    partition_id: str
    split: Split
    asset_id: str
    sha256: str
    content_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    rows: int = Field(ge=3)
    first: datetime
    last: datetime
    median_interval_s: float = Field(gt=0)
    max_gap_s: float = Field(gt=0)
    missing_by_channel: dict[str, int]
    out_of_range_by_channel: dict[str, int]
    gap_count: int = Field(ge=0)


class IntakeReport(Contract):
    schema_version: Literal["1.0"] = "1.0"
    dataset_id: str
    manifest_sha256: str
    source_url: str
    license_identifier: str
    license_note: str
    isolation: Isolation
    embargo_s: int
    provenance_status: Literal["declared_unverified"] = "declared_unverified"
    analysis_status: Literal["not_connected"] = "not_connected"
    partitions: tuple[PartitionSummary, ...]
