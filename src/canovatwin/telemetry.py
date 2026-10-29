"""A seeded, one-zone synthetic plant. Ground truth stays outside agent inputs."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from math import pi, sin
from random import Random

from pydantic import Field

from .contracts import Contract, FaultCode, SensorSample, TelemetryWindow


class Scenario(StrEnum):
    NORMAL = "normal"
    FAN_LOSS = "fan_loss"
    SENSOR_BIAS = "sensor_bias"
    SENSOR_MISSING = "sensor_missing"
    LOAD_SURGE = "load_surge"
    COOLING_LOSS = "cooling_loss"
    AIRFLOW_RESTRICTION = "airflow_restriction"
    FAN_MISMATCH = "fan_mismatch"
    COMMUNICATION_LOSS = "communication_loss"
    CONTROL_OSCILLATION = "control_oscillation"
    COMBINED = "combined"


class TwinConfig(Contract):
    thermal_capacity_kj_per_k: float = Field(default=120.0, gt=0)
    ambient_conductance_kw_per_k: float = Field(default=0.1, ge=0)
    ambient_c: float = Field(default=30.0, ge=-20, le=50)
    target_inlet_c: float = Field(default=23.0, ge=15, le=35)
    nominal_cooling_kw: float = Field(default=10.0, gt=0, le=100)
    nominal_airflow_m3s: float = Field(default=2.5, gt=0, le=20)
    baseline_load_kw: float = Field(default=4.2, ge=0, le=100)
    dt_s: float = Field(default=1.0, gt=0, le=5)


@dataclass(frozen=True)
class ScenarioCase:
    window: TelemetryWindow
    fault_labels: tuple[FaultCode, ...]
    fault_started_at: datetime | None
    observation_time: datetime


_LABELS = {
    Scenario.FAN_LOSS: FaultCode.FAN_LOSS,
    Scenario.SENSOR_BIAS: FaultCode.SENSOR_BIAS,
    Scenario.SENSOR_MISSING: FaultCode.SENSOR_MISSING,
    Scenario.LOAD_SURGE: FaultCode.LOAD_SURGE,
    Scenario.COOLING_LOSS: FaultCode.COOLING_LOSS,
    Scenario.AIRFLOW_RESTRICTION: FaultCode.AIRFLOW_RESTRICTION,
    Scenario.FAN_MISMATCH: FaultCode.FAN_MISMATCH,
    Scenario.COMMUNICATION_LOSS: FaultCode.COMMUNICATION_LOSS,
    Scenario.CONTROL_OSCILLATION: FaultCode.CONTROL_OSCILLATION,
    Scenario.COMBINED: FaultCode.COMBINED,
}


def scenario_labels(scenario: Scenario) -> tuple[FaultCode, ...]:
    """Synthetic ground truth for test harnesses, never supplied to specialists."""
    return () if scenario == Scenario.NORMAL else (_LABELS[scenario],)


def thermal_step(temperature_c: float, load_kw: float, cooling_kw: float, config: TwinConfig) -> float:
    """Forward Euler energy balance, kW = kJ/s; no hidden temperature clamp."""
    ambient_heat_kw = config.ambient_conductance_kw_per_k * (config.ambient_c - temperature_c)
    return (
        temperature_c
        + (load_kw + ambient_heat_kw - cooling_kw) * config.dt_s / config.thermal_capacity_kj_per_k
    )


def generate_case(
    scenario: Scenario = Scenario.NORMAL,
    *,
    count: int = 120,
    seed: int = 42,
    start: datetime | None = None,
    config: TwinConfig | None = None,
) -> ScenarioCase:
    scenario = Scenario(scenario)
    if isinstance(count, bool) or not isinstance(count, int) or not 30 <= count <= 600:
        raise ValueError("count must be an integer between 30 and 600")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    config = config or TwinConfig()
    config = TwinConfig.model_validate(config.model_dump())
    start = start or datetime.now(UTC)
    if start.utcoffset() is None:
        raise ValueError("start must include a timezone")
    rng = Random(seed)
    temperature = config.target_inlet_c
    onset = count // 3
    samples = []
    for i in range(count):
        active = i >= onset
        command = min(100.0, max(20.0, 49.0 + (temperature - config.target_inlet_c) * 15))
        if active and scenario == Scenario.CONTROL_OSCILLATION:
            command = 60.0 + 35.0 * sin(2 * pi * (i - onset) / 10)
        feedback = command
        if active and scenario in (Scenario.FAN_LOSS, Scenario.COMBINED):
            feedback *= 0.45
        if active and scenario == Scenario.FAN_MISMATCH:
            feedback = 20.0
        flow = config.nominal_airflow_m3s * feedback / 100
        if active and scenario == Scenario.AIRFLOW_RESTRICTION:
            flow *= 0.45
        capacity = config.nominal_cooling_kw * flow / config.nominal_airflow_m3s
        if active and scenario in (Scenario.COOLING_LOSS, Scenario.COMBINED):
            capacity *= 0.4
        load = max(0.0, config.baseline_load_kw + rng.uniform(-0.02, 0.02))
        if active and scenario == Scenario.LOAD_SURGE:
            load += 4.2
        inlet = temperature + rng.uniform(-0.03, 0.03)
        reference = temperature + rng.uniform(-0.03, 0.03)
        if active and scenario == Scenario.SENSOR_BIAS:
            inlet += 5.0
        if active and scenario == Scenario.SENSOR_MISSING:
            inlet = None
        timestamp = start + timedelta(seconds=i * config.dt_s)
        # The stream stops, while the simulator's clock continues.
        if not (active and scenario == Scenario.COMMUNICATION_LOSS):
            samples.append(
                SensorSample(
                    sample_id=f"sample-{i:04d}",
                    timestamp=timestamp,
                    inlet_c=inlet,
                    reference_inlet_c=reference,
                    return_c=temperature + load / (1.2 * max(flow, 0.05)),
                    supply_c=temperature - capacity / (1.2 * max(flow, 0.05)),
                    ambient_c=config.ambient_c,
                    humidity_pct=45.0,
                    fan_command_pct=command,
                    fan_feedback_pct=feedback,
                    airflow_m3s=flow,
                    it_load_kw=load,
                    cooling_kw=capacity,
                )
            )
        temperature = thermal_step(temperature, load, capacity, config)
    observation_time = start + timedelta(seconds=(count - 1) * config.dt_s)
    if scenario == Scenario.COMMUNICATION_LOSS:
        # Ensure even a short scenario includes a detectable stale interval.
        observation_time = max(observation_time, samples[-1].timestamp + timedelta(seconds=61))
    return ScenarioCase(
        window=TelemetryWindow(samples=tuple(samples)),
        fault_labels=scenario_labels(scenario),
        fault_started_at=None
        if scenario == Scenario.NORMAL
        else start + timedelta(seconds=onset * config.dt_s),
        observation_time=observation_time,
    )
