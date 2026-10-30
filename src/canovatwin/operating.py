"""Optional dynamic synthetic plant; the original reference generator stays unchanged.

One sensible-heat zone, first-order actuators, prescribed workload and ambient
disturbances. Humidity is an illustrative signal, not a moisture-balance model.
"""

from datetime import timedelta
from math import exp, pi, sin
from random import Random
from typing import Literal

from pydantic import AwareDatetime, Field

from .contracts import Contract, SensorSample, TelemetryWindow
from .telemetry import Scenario, ScenarioCase, TwinConfig, scenario_labels, thermal_step


class OperatingConditions(Contract):
    workload: Literal["steady", "cyclic", "batch"] = "cyclic"
    baseline_load_kw: float = Field(default=4.2, ge=2, le=8)
    ambient_c: float = Field(default=30.0, ge=18, le=40)
    fan_response_s: float = Field(default=6.0, ge=1, le=20)


class GenerationMetadata(Contract):
    """Experiment provenance, deliberately outside AnalysisRequest/agent inputs."""

    generator_version: Literal["dynamic-1.0"] = "dynamic-1.0"
    scenario: Scenario
    count: int = Field(ge=30, le=600)
    seed: int
    start: AwareDatetime
    conditions: OperatingConditions


class ExperimentVariation(Contract):
    """Evaluation-only injection controls; never part of an AnalysisRequest."""

    onset_fraction: float = Field(default=1 / 3, ge=0.1, le=0.85)
    severity: float = Field(default=1.0, ge=0.25, le=1)
    sensor_noise_c: float = Field(default=0.04, ge=0, le=0.5)
    missing_fraction: float = Field(default=1.0, ge=0.2, le=1)


def lag(current: float, target: float, tau_s: float) -> float:
    """Exact first-order step response over one second; cannot overshoot."""
    return target + (current - target) * exp(-1.0 / tau_s)


def workload_kw(time_s: int, conditions: OperatingConditions) -> float:
    if conditions.workload == "cyclic":
        multiplier = 1 + 0.18 * sin(2 * pi * time_s / 90) + 0.06 * sin(2 * pi * time_s / 23)
    elif conditions.workload == "batch":
        # Scheduled 45-second compute jobs, every 120 seconds; finite ramp edges.
        phase = time_s % 120
        multiplier = 1 + 0.35 * max(0, min(1, (phase - 20) / 10, (85 - phase) / 10))
    else:
        multiplier = 1.0
    return conditions.baseline_load_kw * multiplier


def generate_operating_case(metadata: GenerationMetadata) -> ScenarioCase:
    return _generate(metadata, None)


def generate_experiment_case(metadata: GenerationMetadata, variation: ExperimentVariation) -> ScenarioCase:
    variation = ExperimentVariation.model_validate(variation.model_dump())
    return _generate(metadata, variation)


def _generate(metadata: GenerationMetadata, variation: ExperimentVariation | None) -> ScenarioCase:
    metadata = GenerationMetadata.model_validate(metadata.model_dump())
    conditions = metadata.conditions
    scenario = metadata.scenario
    config = TwinConfig(ambient_c=conditions.ambient_c)
    rng = Random(metadata.seed)
    temperature = config.target_inlet_c
    fan = 49.0
    cooling = 4.9
    sensor = temperature
    onset = metadata.count // 3 if variation is None else int(metadata.count * variation.onset_fraction)
    severity = 1.0 if variation is None else variation.severity
    noise = 0.04 if variation is None else variation.sensor_noise_c
    # Missing readings must not alter the physical workload/noise random stream.
    missing_rng = Random(metadata.seed ^ 0x435458)
    samples = []
    for i in range(metadata.count):
        active = i >= onset
        ramp = max(0.0, min(1.0, (i - onset) / 12))
        ambient = conditions.ambient_c + 1.5 * sin(2 * pi * i / 600)
        command = min(100.0, max(20.0, 49.0 + 15 * (temperature - config.target_inlet_c)))
        if active and scenario == Scenario.CONTROL_OSCILLATION:
            command = 60.0 + 35.0 * severity * sin(2 * pi * (i - onset) / 10)
        target_fan = command
        if scenario in (Scenario.FAN_LOSS, Scenario.COMBINED):
            target_fan *= 1 - 0.55 * severity * ramp
        elif scenario == Scenario.FAN_MISMATCH:
            target_fan += (20 - target_fan) * severity * ramp
        fan = lag(fan, target_fan, conditions.fan_response_s)
        flow = config.nominal_airflow_m3s * fan / 100
        if scenario == Scenario.AIRFLOW_RESTRICTION:
            flow *= 1 - 0.55 * severity * ramp
        flow_capacity = config.nominal_cooling_kw * flow / config.nominal_airflow_m3s
        target_cooling = flow_capacity
        if scenario in (Scenario.COOLING_LOSS, Scenario.COMBINED):
            target_cooling *= 1 - 0.6 * severity * ramp
        cooling = min(flow_capacity, lag(cooling, target_cooling, 10.0))
        load = workload_kw(i, conditions) + rng.uniform(-0.04, 0.04)
        if scenario == Scenario.LOAD_SURGE:
            load += 4.2 * severity * ramp
        sensor = lag(sensor, temperature, 2.0)
        inlet = sensor + rng.uniform(-noise, noise)
        if scenario == Scenario.SENSOR_BIAS:
            inlet += 5.0 * severity * ramp
        if (
            active
            and scenario == Scenario.SENSOR_MISSING
            and (variation is None or missing_rng.random() < variation.missing_fraction)
        ):
            inlet = None
        if not (active and scenario == Scenario.COMMUNICATION_LOSS):
            samples.append(
                SensorSample(
                    sample_id=f"sample-{i:04d}",
                    timestamp=metadata.start + timedelta(seconds=i),
                    inlet_c=inlet,
                    reference_inlet_c=temperature,
                    return_c=temperature + load / (1.2 * max(flow, 0.05)),
                    supply_c=temperature - cooling / (1.2 * max(flow, 0.05)),
                    ambient_c=ambient,
                    humidity_pct=45 + 2.5 * sin(2 * pi * i / 180) + rng.uniform(-0.2, 0.2),
                    fan_command_pct=command,
                    fan_feedback_pct=fan,
                    airflow_m3s=flow,
                    it_load_kw=load,
                    cooling_kw=cooling,
                )
            )
        temperature = thermal_step(
            temperature, load, cooling, config.model_copy(update={"ambient_c": ambient})
        )
    observation_time = metadata.start + timedelta(seconds=metadata.count - 1)
    if scenario == Scenario.COMMUNICATION_LOSS:
        observation_time = max(observation_time, samples[-1].timestamp + timedelta(seconds=61))
    return ScenarioCase(
        window=TelemetryWindow(samples=tuple(samples)),
        fault_labels=scenario_labels(scenario),
        fault_started_at=None if scenario == Scenario.NORMAL else metadata.start + timedelta(seconds=onset),
        observation_time=observation_time,
    )
