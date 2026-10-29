from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from canovatwin.contracts import AnalysisRequest, AnalysisRun
from canovatwin.policy import Policy
from canovatwin.registry import ACTIVE_IDS, BY_ID, REGISTRY
from canovatwin.supervisor import Supervisor


def test_canonical_registry():
    assert len(REGISTRY) == len(BY_ID) == 36
    assert set(BY_ID) == {f"{g}0{i}" for g in "ABCDEF" for i in range(1, 7)}
    assert ACTIVE_IDS == ("A02", "A03", "A06", "B02", "B03", "B05", "B06", "D02", "D06", "F02", "F03", "F04")
    assert {s.agent_id for s in REGISTRY if s.activation_stage == 12} == {
        "A06",
        "B05",
        "B06",
        "D02",
        "D06",
        "F02",
    }
    assert all(
        s.status == "planned" and not s.allowed_tools for s in REGISTRY if s.agent_id not in ACTIVE_IDS
    )
    with pytest.raises(TypeError):
        BY_ID["A02"] = BY_ID["A03"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("inlet_c", float("nan")),
        ("inlet_c", float("inf")),
        ("inlet_c", "23"),
        ("inlet_c", True),
        ("timestamp", datetime(2026, 10, 28)),
        ("unknown", 0),
    ],
)
def test_strict_sensor_boundary(request_factory, field, value):
    data = request_factory().model_dump()
    samples = list(data["window"]["samples"])
    samples[0][field] = value
    data["window"]["samples"] = tuple(samples)
    with pytest.raises(ValidationError):
        AnalysisRequest.model_validate(data)


def test_source_and_label_boundaries(request_factory):
    for field, value in [("source", "plc"), ("fault_labels", ("FAULT_F01",))]:
        data = request_factory().model_dump()
        data["window"][field] = value
        with pytest.raises(ValidationError):
            AnalysisRequest.model_validate(data)


def test_construct_and_copy_bypasses_are_revalidated(request_factory):
    request = request_factory()
    window = request.window.model_copy(update={"source": "plc"})
    with pytest.raises(ValidationError):
        Supervisor().run(request.model_copy(update={"window": window}))
    with pytest.raises(ValidationError):
        Supervisor(Policy.model_construct(max_agents=99)).run(request)


@pytest.mark.parametrize(
    ("age", "expected"), [(60, "clear"), (61, "insufficient_data"), (-5, "clear"), (-6, "insufficient_data")]
)
def test_freshness_applies_to_latest_sample_not_entire_history(request_factory, age, expected):
    request = request_factory()
    request = request.model_copy(
        update={"as_of": request.window.samples[-1].timestamp + timedelta(seconds=age)}
    )
    assert Supervisor().run(request).report.status == expected


@pytest.mark.parametrize(
    "problem", ["missing", "range", "temperature_order", "duplicate_id", "duplicate_time", "reversed", "gap"]
)
def test_quality_failures_produce_report_without_diagnosis(request_factory, problem):
    request = request_factory()
    samples = list(request.window.samples)
    change = {
        "missing": {"inlet_c": None},
        "range": {"humidity_pct": 101.0},
        "temperature_order": {"supply_c": 25.0, "return_c": 20.0},
        "duplicate_id": {"sample_id": samples[1].sample_id},
        "duplicate_time": {"timestamp": samples[1].timestamp},
        "reversed": {"timestamp": samples[2].timestamp},
        "gap": {"timestamp": samples[0].timestamp - timedelta(seconds=10)},
    }[problem]
    samples[0] = samples[0].model_copy(update=change)
    request = request.model_copy(
        update={"window": request.window.model_copy(update={"samples": tuple(samples)})}
    )
    run = Supervisor().run(request)
    assert run.status == "completed" and run.report.status == "insufficient_data"
    assert run.report.observations and not run.report.hypotheses
    assert tuple(t.agent_id for t in run.trace) == ("A02", "F03", "F04")


def test_window_limit(request_factory):
    run = Supervisor(Policy(max_window_s=30.0)).run(request_factory())
    assert run.report.status == "insufficient_data"
    assert "QUALITY_WINDOW_SPAN_S" in {o.code for o in run.report.observations}


def test_request_timezone(request_factory):
    with pytest.raises(ValidationError):
        AnalysisRequest(window=request_factory().window, as_of=datetime(2026, 10, 28))


@pytest.mark.parametrize(
    "change",
    [dict(max_agents=0), dict(max_elapsed_s=float("inf")), dict(max_gap_s=4000.0), dict(max_tool_calls="6")],
)
def test_policy_is_validated(change):
    with pytest.raises(ValidationError):
        Policy(**change)


def test_report_cannot_carry_commands_or_inconsistent_status(request_factory):
    data = Supervisor().run(request_factory()).model_dump()
    for change in [dict(commands=("start_fan",)), dict(status="blocked"), dict(report=None)]:
        with pytest.raises(ValidationError):
            AnalysisRun.model_validate(data | change)
