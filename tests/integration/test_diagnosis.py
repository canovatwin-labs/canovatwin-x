import pytest

from canovatwin.contracts import AnalysisRequest, AnalysisRun, FaultCode, VerificationResult
from canovatwin.supervisor import Supervisor
from canovatwin.telemetry import Scenario


@pytest.mark.parametrize(
    ("scenario", "status", "cause"),
    [
        (Scenario.NORMAL, "clear", None),
        (Scenario.FAN_LOSS, "needs_review", FaultCode.FAN_LOSS),
        (Scenario.SENSOR_BIAS, "needs_review", FaultCode.SENSOR_BIAS),
        (Scenario.SENSOR_MISSING, "insufficient_data", None),
        (Scenario.LOAD_SURGE, "needs_review", FaultCode.LOAD_SURGE),
        (Scenario.COOLING_LOSS, "needs_review", FaultCode.COOLING_LOSS),
        (Scenario.AIRFLOW_RESTRICTION, "needs_review", FaultCode.AIRFLOW_RESTRICTION),
        (Scenario.FAN_MISMATCH, "needs_review", FaultCode.FAN_MISMATCH),
        (Scenario.COMMUNICATION_LOSS, "insufficient_data", None),
        (Scenario.CONTROL_OSCILLATION, "needs_review", FaultCode.CONTROL_OSCILLATION),
        (Scenario.COMBINED, "needs_review", FaultCode.COOLING_LOSS),
    ],
)
def test_all_scenarios(request_factory, scenario, status, cause):
    run = Supervisor().run(request_factory(scenario))
    assert run.status == "completed"
    assert run.report.status == status
    assert run.commands == () and run.llm_calls == 0
    assert run.total_tool_calls == sum(t.tool_calls for t in run.trace)
    assert all(t.status == "completed" for t in run.trace)
    assert AnalysisRun.model_validate_json(run.model_dump_json()) == run
    ids = tuple(t.agent_id for t in run.trace)
    if status == "clear":
        assert ids == ("A02", "A03", "B02", "F03", "F04")
    elif status == "insufficient_data":
        assert ids == ("A02", "F03", "F04")
        assert not run.report.hypotheses
    else:
        assert ids == ("A02", "A03", "B02", "B03", "F03", "F04")
    if cause:
        assert cause in {h.fault_code for h in run.report.hypotheses}
    verified = next(o.payload for o in run.outputs if isinstance(o.payload, VerificationResult))
    assert verified.passed
    assert verified.checked_evidence_ids == run.report.evidence_ids
    evidence_ids = {e.evidence_id for e in run.evidence}
    assert len(evidence_ids) == len(run.evidence)
    for h in run.report.hypotheses:
        assert set(h.supporting_evidence + h.contradicting_evidence) <= evidence_ids


@pytest.mark.parametrize("scenario", list(Scenario)[1:])
def test_before_fault_is_normal(case_factory, scenario):
    case = case_factory(scenario)
    baseline = tuple(s for s in case.window.samples if s.timestamp < case.fault_started_at)
    request = AnalysisRequest(
        window=case.window.model_copy(update={"samples": baseline}), as_of=baseline[-1].timestamp
    )
    assert Supervisor().run(request).report.status == "clear"


def test_evidence_counterclaims_preserved(request_factory):
    report = Supervisor().run(request_factory(Scenario.COOLING_LOSS)).report
    weak_load_candidate = next(h for h in report.hypotheses if h.fault_code == FaultCode.LOAD_SURGE)
    assert weak_load_candidate.assessment == "uncertain"
    assert weak_load_candidate.contradicting_evidence


def test_repeated_runs_are_isolated_and_reproducible(request_factory):
    supervisor = Supervisor()
    normal = request_factory()
    first = supervisor.run(normal)
    fault = supervisor.run(request_factory(Scenario.FAN_LOSS))
    second = supervisor.run(normal)
    assert first.report == second.report
    assert first.outputs == second.outputs
    assert first.incident_id == second.incident_id != fault.incident_id
    assert first.total_tool_calls == second.total_tool_calls == 5


def test_humidity_has_no_invented_root_cause(request_factory):
    request = request_factory()
    window = request.window.model_copy(
        update={"samples": tuple(s.model_copy(update={"humidity_pct": 85.0}) for s in request.window.samples)}
    )
    run = Supervisor().run(request.model_copy(update={"window": window}))
    assert run.report.status == "needs_review"
    assert not run.report.hypotheses
    assert any("kök neden" in message for message in run.report.limitations)


def test_labels_never_enter_agent_contracts(case_factory):
    for scenario in Scenario:
        case = case_factory(scenario)
        request = AnalysisRequest(window=case.window, as_of=case.observation_time)
        payload = request.model_dump_json()
        assert "fault_labels" not in payload and "fault_started_at" not in payload
        assert all(label.value not in payload for label in case.fault_labels)
        assert all(s.sample_id.startswith("sample-") for s in request.window.samples)
