from datetime import UTC, datetime
from math import exp

import pytest
from pydantic import ValidationError

from canovatwin.operating import (
    GenerationMetadata,
    OperatingConditions,
    generate_operating_case,
    lag,
    workload_kw,
)
from canovatwin.telemetry import Scenario


def experiment(scenario=Scenario.NORMAL, **conditions):
    return GenerationMetadata(
        scenario=scenario,
        count=360,
        seed=42,
        start=datetime(2026, 10, 28, tzinfo=UTC),
        conditions=OperatingConditions(**conditions),
    )


def test_seed_reproduction_and_independent_noise():
    spec = experiment()
    first = generate_operating_case(spec)
    assert first == generate_operating_case(spec)
    assert first != generate_operating_case(spec.model_copy(update={"seed": 43}))


def test_first_order_response_matches_hand_calculation_and_does_not_overshoot():
    assert lag(0, 100, 5) == pytest.approx(100 * (1 - exp(-0.2)))
    assert 20 < lag(80, 20, 6) < 80


def test_dynamic_energy_balance_at_every_step():
    samples = generate_operating_case(experiment(Scenario.COMBINED)).window.samples
    for before, after in zip(samples[:-1], samples[1:], strict=True):
        expected = (
            before.reference_inlet_c
            + (before.it_load_kw + 0.1 * (before.ambient_c - before.reference_inlet_c) - before.cooling_kw)
            / 120
        )
        assert after.reference_inlet_c == pytest.approx(expected, abs=1e-12)
        assert 0 <= before.cooling_kw <= before.airflow_m3s * 4
        assert 0 <= before.fan_feedback_pct <= 100


def test_workload_profiles_have_distinct_known_shapes():
    assert workload_kw(30, OperatingConditions(workload="steady")) == 4.2
    batch = OperatingConditions(workload="batch")
    assert workload_kw(10, batch) == 4.2
    assert workload_kw(30, batch) == pytest.approx(4.2 * 1.35)
    assert workload_kw(90, batch) == 4.2
    assert workload_kw(30, OperatingConditions()) != 4.2


def test_fault_ramp_and_actuator_lag_are_not_instantaneous():
    spec = experiment(Scenario.FAN_LOSS, workload="steady")
    samples = generate_operating_case(spec).window.samples
    onset = spec.count // 3
    assert abs(samples[onset].fan_feedback_pct - samples[onset - 1].fan_feedback_pct) < 1
    assert samples[onset + 30].fan_feedback_pct < samples[onset + 30].fan_command_pct * 0.7
    assert len({s.ambient_c for s in samples}) > 100
    assert len({s.humidity_pct for s in samples}) > 100


def test_gaps_are_preserved_and_clock_keeps_advancing():
    missing = generate_operating_case(experiment(Scenario.SENSOR_MISSING))
    assert all(s.inlet_c is None for s in missing.window.samples[120:])
    stopped = generate_operating_case(experiment(Scenario.COMMUNICATION_LOSS))
    assert len(stopped.window.samples) == 120
    assert (stopped.observation_time - stopped.window.samples[-1].timestamp).total_seconds() == 240


@pytest.mark.parametrize(
    "conditions",
    [
        {"baseline_load_kw": 0.0},
        {"baseline_load_kw": 8.1},
        {"ambient_c": 41.0},
        {"fan_response_s": 0.0},
        {"fan_response_s": float("nan")},
        {"workload": "unknown"},
    ],
)
def test_invalid_conditions_rejected(conditions):
    with pytest.raises(ValidationError):
        OperatingConditions(**conditions)


@pytest.mark.parametrize("count", [30, 600])
@pytest.mark.parametrize("scenario", list(Scenario))
def test_plant_contract_at_duration_and_operating_limits(count, scenario):
    spec = experiment(scenario, workload="batch", baseline_load_kw=8.0, ambient_c=40.0, fan_response_s=20.0)
    result = generate_operating_case(spec.model_copy(update={"count": count}))
    assert len(result.window.samples) == (count // 3 if scenario == Scenario.COMMUNICATION_LOSS else count)
    assert all(0 <= s.fan_feedback_pct <= 100 and s.it_load_kw >= 0 for s in result.window.samples)
    assert all(0 <= s.cooling_kw <= 10 for s in result.window.samples)
