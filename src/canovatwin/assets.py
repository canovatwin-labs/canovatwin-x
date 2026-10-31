"""Versioned synthetic asset definitions and observed history inventory contracts."""

from typing import Literal

from pydantic import AwareDatetime, Field

from .analysis.quality import BOUNDS
from .contracts import Contract, Identifier
from .operating import OperatingConditions

DEFAULT_ASSET = "synthetic-unit-01"


class AssetDefinition(Contract):
    asset_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,100}$")
    name: str = Field(min_length=1, max_length=100)
    location: str = Field(min_length=1, max_length=100)
    source: Literal["synthetic"] = "synthetic"
    model: Literal["single-zone-10kW"] = "single-zone-10kW"
    expected_interval_s: Literal[1] = 1
    default_conditions: OperatingConditions = OperatingConditions()


DEFAULT_ASSETS = (
    AssetDefinition(asset_id=DEFAULT_ASSET, name="Pilot soğutma ünitesi 01", location="Sentetik pilot alan"),
    AssetDefinition(
        asset_id="synthetic-unit-02",
        name="Pilot soğutma ünitesi 02",
        location="Sentetik pilot alan",
        default_conditions=OperatingConditions(workload="batch", baseline_load_kw=6),
    ),
)


class AssetRollup(Contract):
    asset_id: Identifier
    incident_count: int = Field(ge=0)
    open_incident_count: int = Field(ge=0)
    run_count: int = Field(ge=0)
    latest_run_id: Identifier | None
    last_recorded_at: AwareDatetime | None


class AssetSummary(AssetRollup):
    definition: AssetDefinition | None = None


class ChannelDefinition(Contract):
    field: str
    name: str
    unit: str
    illustrative_min: float
    illustrative_max: float


CHANNEL_NAMES = {
    "inlet_c": ("Giriş sıcaklığı", "°C"),
    "reference_inlet_c": ("Referans giriş sıcaklığı", "°C"),
    "return_c": ("Dönüş sıcaklığı", "°C"),
    "supply_c": ("Besleme sıcaklığı", "°C"),
    "ambient_c": ("Ortam sıcaklığı", "°C"),
    "humidity_pct": ("Bağıl nem", "%"),
    "fan_command_pct": ("Fan komutu", "%"),
    "fan_feedback_pct": ("Fan geri bildirimi", "%"),
    "airflow_m3s": ("Hava debisi", "m³/sn"),
    "it_load_kw": ("IT yükü", "kW"),
    "cooling_kw": ("Termal soğutma gücü", "kW"),
}
CHANNELS = tuple(
    ChannelDefinition(
        field=field,
        name=CHANNEL_NAMES[field][0],
        unit=CHANNEL_NAMES[field][1],
        illustrative_min=low,
        illustrative_max=high,
    )
    for field, (low, high) in BOUNDS.items()
)


class AssetDetail(Contract):
    catalog_version: Literal["catalog-1.0"] = "catalog-1.0"
    asset: AssetSummary
    channels: tuple[ChannelDefinition, ...] = CHANNELS
