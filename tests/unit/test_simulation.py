from datetime import datetime

import pytest

from canovatwin.contracts import AnalysisRequest
from canovatwin.supervisor import Supervisor
from canovatwin.telemetry import Scenario, TwinConfig, generate_case, thermal_step


def test_energy_conservation():
    config = TwinConfig(thermal_capacity_kj_per_k=100.0, ambient_conductance_kw_per_k=0.0, dt_s=2.0)
    assert thermal_step(25.0, 10.0, 5.0, config) == pytest.approx(25.1)
    assert thermal_step(25.0, 5.0, 5.0, config) == 25.0
    assert thermal_step(25.0, 5.0, 10.0, config) == pytest.approx(24.9)


def test_ambient_heat_transfer():
    config = TwinConfig(
        thermal_capacity_kj_per_k=100.0, ambient_conductance_kw_per_k=1.0, ambient_c=30.0, dt_s=1.0
    )
    assert thermal_step(20.0, 0.0, 0.0, config) == pytest.approx(20.1)


def test_seeded_simulation(case_factory):
    assert case_factory(Scenario.FAN_LOSS) == case_factory(Scenario.FAN_LOSS)
    assert case_factory(seed=1).window != case_factory(seed=2).window


@pytest.mark.parametrize("count", [0, 29, 601, True, 1.5])
def test_sample_count_bounds(count):
    with pytest.raises(ValueError):
        generate_case(count=count)


@pytest.mark.parametrize(
    "kwargs", [dict(seed=True), dict(seed="42"), dict(start=datetime(2026, 10, 28)), dict(scenario="unknown")]
)
def test_generator_input_validation(kwargs):
    with pytest.raises(ValueError):
        generate_case(**kwargs)


@pytest.mark.parametrize("scenario", list(Scenario))
def test_longest_scenario_stays_valid(case_factory, scenario):
    case = case_factory(scenario, count=600)
    run = Supervisor().run(AnalysisRequest(window=case.window, as_of=case.observation_time))
    assert run.status == "completed"


def test_hand_computed_window_statistics(request_factory):
    request = request_factory()
    temperatures = [23.0, 23.0, 24.0, 25.0, 26.0, 26.0]
    samples = tuple(
        sample.model_copy(
            update={
                "inlet_c": temperatures[i],
                "reference_inlet_c": temperatures[i],
                "it_load_kw": 3.0 if i < 2 else 6.0,
                "fan_command_pct": 60.0,
                "fan_feedback_pct": 60.0,
                "airflow_m3s": 1.5,
                "cooling_kw": 6.0,
            }
        )
        for i, sample in enumerate(request.window.samples[:6])
    )
    request = AnalysisRequest(
        window=request.window.model_copy(update={"samples": samples}), as_of=samples[-1].timestamp
    )
    run = Supervisor().run(request)
    metrics = {e.metric: e.value for e in run.evidence}
    assert metrics["inlet_rise_c"] == 3.0
    assert metrics["load_increase_kw"] == 3.0
    assert metrics["fan_error_pct"] == 0.0
    assert metrics["airflow_efficiency"] == 1.0
    assert metrics["cooling_efficiency"] == 1.0
    assert metrics["inlet_slope_c_per_min"] == pytest.approx((12.5 / 17.5) * 60)


def test_variance_and_correlation_have_known_values(request_factory):
    request = request_factory()
    samples = tuple(
        s.model_copy(update={"inlet_c": float(20 + i), "fan_feedback_pct": float(20 + i * 10)})
        for i, s in enumerate(request.window.samples[:3])
    )
    request = AnalysisRequest(
        window=request.window.model_copy(update={"samples": samples}), as_of=samples[-1].timestamp
    )
    run = Supervisor().run(request)
    metrics = {e.metric: e.value for e in run.evidence}
    assert metrics["inlet_variance_c2"] == pytest.approx(2 / 3)
    assert metrics["fan_temperature_correlation"] == pytest.approx(1.0)


def test_zero_load_does_not_generate_negative_heat(case_factory):
    case = case_factory(config=TwinConfig(baseline_load_kw=0.0))
    assert all(sample.it_load_kw >= 0 for sample in case.window.samples)
