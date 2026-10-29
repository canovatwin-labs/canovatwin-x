from dataclasses import replace

import pytest

from canovatwin.agents import (
    AnomalyInvestigator,
    EvidenceVerifier,
    ReportComposer,
    RootCauseAnalyst,
    SensorValidator,
    SignalAnalyzer,
    build_specialist,
)
from canovatwin.analysis.evidence import verify
from canovatwin.analysis.quality import check_quality
from canovatwin.analysis.reporting import compose_report
from canovatwin.analysis.signals import analyze_signals
from canovatwin.contracts import AnomalyResult, DiagnosisResult, FaultCode
from canovatwin.policy import Policy
from canovatwin.registry import BY_ID
from canovatwin.runtime import Budget, ExecutionError, ToolSession
from canovatwin.state import AnalysisContext
from canovatwin.supervisor import Supervisor
from canovatwin.telemetry import Scenario


def test_inactive_roles_cannot_be_instantiated():
    with pytest.raises(ValueError, match="not implemented"):
        build_specialist("E02")


@pytest.mark.parametrize(
    ("policy", "error_code"),
    [
        (Policy(max_agents=1), "AGENT_BUDGET_EXCEEDED"),
        (Policy(max_tool_calls=1), "TOOL_BUDGET_EXCEEDED"),
    ],
)
def test_total_budgets_fail_closed(request_factory, policy, error_code):
    run = Supervisor(policy).run(request_factory())
    assert run.status == "blocked" and run.report is None
    assert run.failure.code == error_code
    assert run.total_tool_calls == 1
    assert run.trace[-1].status == "failed"


def test_per_agent_budget_and_authorization(request_factory):
    policy = Policy()
    ctx = AnalysisContext("INC-test", request_factory(), policy)
    session = ToolSession(BY_ID["A02"], ctx, Budget(policy))
    with pytest.raises(ExecutionError, match="not permitted"):
        session.call("evaluate_causes")
    with pytest.raises(ExecutionError, match="not permitted"):
        session.call("write_plc")
    assert session.calls == 0
    session.call("check_sensor_quality")
    with pytest.raises(ExecutionError, match="Specialist tool budget"):
        session.call("check_sensor_quality")
    assert session.calls == 1


def test_deadline_checked_after_tool_work(request_factory, monkeypatch):
    clock = [0.0]
    original = SensorValidator.execute

    def delayed(self, tools):
        result = original(self, tools)
        clock[0] = 10.0
        return result

    monkeypatch.setattr(SensorValidator, "execute", delayed)
    run = Supervisor(clock=lambda: clock[0]).run(request_factory())
    assert run.status == "blocked" and run.report is None
    assert run.failure.code == "DEADLINE_EXCEEDED"


def test_tool_deadline_checked_before_and_after_call(request_factory, monkeypatch):
    policy = Policy(max_elapsed_s=1.0)
    clock = [0.0]
    budget = Budget(policy, clock=lambda: clock[0])
    ctx = AnalysisContext("INC-test", request_factory(), policy)
    session = ToolSession(BY_ID["A02"], ctx, budget)
    clock[0] = 2.0
    with pytest.raises(ExecutionError):
        session.call("check_sensor_quality")
    assert session.calls == 0


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ("producer", "EVIDENCE_PRODUCER_MISMATCH"),
        ("duplicate", "DUPLICATE_EVIDENCE"),
        ("numeric", "EVIDENCE_VERIFICATION_FAILED"),
        ("missing", "EVIDENCE_VERIFICATION_FAILED"),
        ("schema", "OUTPUT_SCHEMA_MISMATCH"),
        ("invalid", "INVALID_AGENT_OUTPUT"),
    ],
)
def test_tampered_quality_outputs_fail_closed(request_factory, monkeypatch, mutation, code):
    original = SensorValidator.execute

    def altered(self, tools):
        result = original(self, tools)
        if mutation == "invalid":
            return {"commands": ["start_fan"]}
        if mutation == "schema":
            return AnomalyResult(detected=False, observations=())
        evidence = result.evidence
        if mutation == "producer":
            evidence = (evidence[0].model_copy(update={"producer": "B03"}),) + evidence[1:]
        elif mutation == "duplicate":
            evidence += (evidence[0],)
        elif mutation == "numeric":
            evidence = (evidence[0].model_copy(update={"value": 999.0}),) + evidence[1:]
        elif mutation == "missing":
            evidence = evidence[1:]
        return result.model_copy(update={"evidence": evidence})

    monkeypatch.setattr(SensorValidator, "execute", altered)
    run = Supervisor().run(request_factory())
    assert run.status == "blocked" and run.report is None
    assert run.failure.code == code
    assert run.commands == ()


def test_unexecuted_tool_is_rejected(request_factory, monkeypatch):
    ctx = AnalysisContext("INC-test", request_factory(), Policy())
    monkeypatch.setattr(SensorValidator, "execute", lambda self, tools: check_quality(ctx))
    run = Supervisor().run(ctx.request)
    assert run.failure.code == "MISSING_TOOL_EXECUTION"


def test_suppressed_anomaly_is_caught(request_factory, monkeypatch):
    original = AnomalyInvestigator.execute

    def suppress(self, tools):
        original(self, tools)
        return AnomalyResult(detected=False, observations=())

    monkeypatch.setattr(AnomalyInvestigator, "execute", suppress)
    run = Supervisor().run(request_factory(Scenario.LOAD_SURGE))
    assert run.failure.code == "EVIDENCE_VERIFICATION_FAILED"
    assert run.report is None


def test_fake_evidence_reference_is_caught(request_factory, monkeypatch):
    original = RootCauseAnalyst.execute

    def alter(self, tools):
        result = original(self, tools)
        hypothesis = result.hypotheses[0].model_copy(update={"supporting_evidence": ("EV-not-real",)})
        return DiagnosisResult(hypotheses=(hypothesis,))

    monkeypatch.setattr(RootCauseAnalyst, "execute", alter)
    run = Supervisor().run(request_factory(Scenario.LOAD_SURGE))
    assert run.failure.code == "EVIDENCE_VERIFICATION_FAILED"
    verifier_output = next(o.payload for o in run.outputs if o.agent_id == "F03")
    assert any("unknown evidence" in e for e in verifier_output.errors)


def test_fabricated_diagnosis_is_caught(request_factory, monkeypatch):
    original = RootCauseAnalyst.execute

    def alter(self, tools):
        result = original(self, tools)
        candidate = result.hypotheses[0].model_copy(update={"fault_code": FaultCode.CONTROL_OSCILLATION})
        return DiagnosisResult(hypotheses=(candidate,))

    monkeypatch.setattr(RootCauseAnalyst, "execute", alter)
    run = Supervisor().run(request_factory(Scenario.LOAD_SURGE))
    assert run.failure.code == "EVIDENCE_VERIFICATION_FAILED"


def test_verifier_cannot_invent_a_verdict(request_factory, monkeypatch):
    original = EvidenceVerifier.execute

    def alter(self, tools):
        result = original(self, tools)
        return result.model_copy(update={"checked_evidence_ids": ()})

    monkeypatch.setattr(EvidenceVerifier, "execute", alter)
    run = Supervisor().run(request_factory())
    assert run.failure.code == "VERIFIER_OUTPUT_MISMATCH"


def test_report_cannot_change_verified_claims(request_factory, monkeypatch):
    original = ReportComposer.execute

    def alter(self, tools):
        result = original(self, tools)
        return result.model_copy(update={"summary": "Unproven claim"})

    monkeypatch.setattr(ReportComposer, "execute", alter)
    run = Supervisor().run(request_factory())
    assert run.failure.code == "REPORT_VALIDATION_FAILED"
    assert run.report is None


def test_exceptions_are_redacted_and_do_not_poison_next_run(request_factory, monkeypatch):
    def crash(self, tools):
        raise RuntimeError("private-company-secret")

    with monkeypatch.context() as patch:
        patch.setattr(SensorValidator, "execute", crash)
        run = Supervisor().run(request_factory())
        assert run.failure.code == "AGENT_EXECUTION_FAILED"
        assert "private-company-secret" not in run.model_dump_json()
    assert Supervisor().run(request_factory()).status == "completed"


def test_altered_statistics_are_recomputed(request_factory, monkeypatch):
    original = SignalAnalyzer.execute

    def alter(self, tools):
        result = original(self, tools)
        first = result.evidence[0].model_copy(update={"value": 80.0})
        return result.model_copy(update={"evidence": (first,) + result.evidence[1:]})

    monkeypatch.setattr(SignalAnalyzer, "execute", alter)
    assert Supervisor().run(request_factory()).failure.code == "EVIDENCE_VERIFICATION_FAILED"


def test_tool_preconditions_and_verification_gate(request_factory):
    ctx = AnalysisContext("INC-test", request_factory(), Policy())
    with pytest.raises(ValueError):
        analyze_signals(ctx)
    with pytest.raises(ValueError):
        compose_report(ctx)
    quality = check_quality(ctx)
    ctx = replace(ctx, quality=quality, evidence=quality.evidence)
    verdict = verify(ctx)
    assert verdict.passed
    ctx = replace(ctx, verification=verdict, evidence=())
    with pytest.raises(ValueError, match="changed after verification"):
        compose_report(ctx)
