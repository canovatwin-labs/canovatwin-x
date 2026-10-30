"""Global coordinator: route by data quality/anomaly, then verify before reporting."""

from collections.abc import Callable
from dataclasses import replace
from time import monotonic

from pydantic import ValidationError

from .agents import build_specialist
from .analysis.evidence import verify
from .analysis.reporting import compose_report
from .contracts import (
    AgentOutput,
    AgentRun,
    AnalysisRequest,
    AnalysisRun,
    AnomalyResult,
    CritiqueResult,
    DiagnosisResult,
    HistoricalResult,
    MissingDataResult,
    QualityResult,
    RetrievalResult,
    RunFailure,
    SignalResult,
    SimulationResult,
    SimulationValidationResult,
    TechnicalReport,
    VerificationResult,
)
from .identity import incident_identifier
from .policy import Policy, default_policy
from .registry import BY_ID
from .runtime import Budget, ExecutionError, ToolSession
from .state import AnalysisContext

_STATE_FIELDS = {
    QualityResult: "quality",
    SignalResult: "signals",
    AnomalyResult: "anomaly",
    DiagnosisResult: "diagnosis",
    VerificationResult: "verification",
    MissingDataResult: "missing_data",
    HistoricalResult: "history",
    RetrievalResult: "retrieval",
    CritiqueResult: "critique",
    SimulationResult: "simulation",
    SimulationValidationResult: "simulation_validation",
}


class Supervisor:
    def __init__(self, policy: Policy | None = None, *, clock: Callable[[], float] = monotonic):
        self.policy = policy
        self._clock = clock

    def run(self, request: AnalysisRequest) -> AnalysisRun:
        # model_construct / model_copy can bypass validation; validate recursively at ingress.
        request = AnalysisRequest.model_validate(request.model_dump())
        policy = Policy.model_validate((self.policy or default_policy(request)).model_dump())
        incident_id = incident_identifier(request, policy)
        digest = incident_id[4:]
        ctx = AnalysisContext(incident_id, request, policy)
        budget = Budget(policy, clock=self._clock)
        outputs, trace = [], []
        report = None
        failure = None
        agent_id = "A02"
        while agent_id:
            task_id = f"TASK-{digest}-{agent_id}"
            started = self._clock()
            session = None
            error = None
            try:
                budget.begin_agent()
                definition = BY_ID[agent_id]
                if definition.status != "active":
                    raise ExecutionError("AGENT_DISABLED", "Requested specialist is not active")
                session = ToolSession(definition, ctx, budget)
                payload = build_specialist(agent_id).execute(session)
                output = AgentOutput.model_validate(
                    {
                        "agent_id": agent_id,
                        "task_id": task_id,
                        "incident_id": incident_id,
                        "payload": payload.model_dump(),
                    }
                )
                payload = output.payload
                if payload.kind != definition.output_schema:
                    raise ExecutionError(
                        "OUTPUT_SCHEMA_MISMATCH", "Specialist returned another role's output"
                    )
                if session.calls != 1:
                    raise ExecutionError(
                        "MISSING_TOOL_EXECUTION", "Specialist did not execute its registered tool"
                    )
                if isinstance(
                    payload,
                    (
                        QualityResult,
                        SignalResult,
                        MissingDataResult,
                        HistoricalResult,
                        RetrievalResult,
                        SimulationResult,
                        SimulationValidationResult,
                    ),
                ):
                    if any(e.producer != agent_id for e in payload.evidence):
                        raise ExecutionError(
                            "EVIDENCE_PRODUCER_MISMATCH", "Evidence producer does not match its task"
                        )
                    ids = [e.evidence_id for e in ctx.evidence + payload.evidence]
                    if len(ids) != len(set(ids)):
                        raise ExecutionError("DUPLICATE_EVIDENCE", "Evidence IDs must be unique")
                    ctx = replace(ctx, evidence=ctx.evidence + payload.evidence)
                if isinstance(payload, VerificationResult) and payload != verify(ctx):
                    raise ExecutionError(
                        "VERIFIER_OUTPUT_MISMATCH", "Verifier returned an unsupported verdict"
                    )
                field = _STATE_FIELDS.get(type(payload))
                if field:
                    ctx = replace(ctx, **{field: payload})
                outputs.append(output)
                if isinstance(payload, VerificationResult) and not payload.passed:
                    raise ExecutionError(
                        "EVIDENCE_VERIFICATION_FAILED", "Evidence or claims failed independent checks"
                    )
                if isinstance(payload, TechnicalReport):
                    if payload != compose_report(ctx):
                        raise ExecutionError(
                            "REPORT_VALIDATION_FAILED", "Report differs from verified findings"
                        )
                    report = payload
                budget.check_deadline()
            except ExecutionError as exc:
                error = RunFailure(code=exc.code, message=str(exc))
            except (ValidationError, AttributeError, TypeError, ValueError):
                error = RunFailure(
                    code="INVALID_AGENT_OUTPUT",
                    message="Specialist returned invalid data or violated a precondition",
                )
            except Exception:
                error = RunFailure(code="AGENT_EXECUTION_FAILED", message="Specialist execution failed")
            trace.append(
                AgentRun(
                    agent_id=agent_id,
                    task_id=task_id,
                    status="failed" if error else "completed",
                    tool_calls=session.calls if session else 0,
                    elapsed_ms=max(0.0, (self._clock() - started) * 1000),
                    error_code=error.code if error else None,
                )
            )
            if error:
                failure, report = error, None
                break
            agent_id = self._next(agent_id, ctx)
        return AnalysisRun(
            incident_id=incident_id,
            mode="external_review" if request.window.source == "declared_external" else "simulation",
            clock_mode=request.clock_mode,
            status="blocked" if failure else "completed",
            report=report,
            outputs=tuple(outputs),
            trace=tuple(trace),
            evidence=ctx.evidence,
            failure=failure,
            total_tool_calls=budget.tool_calls,
        )

    @staticmethod
    def _next(agent_id: str, ctx: AnalysisContext) -> str | None:
        extended = ctx.request.research is not None
        if agent_id == "A02":
            return "A03" if ctx.quality and ctx.quality.usable else "A06" if extended else "F03"
        if agent_id == "A03":
            return "B02"
        if agent_id == "B02":
            if not ctx.anomaly or not ctx.anomaly.detected:
                return "F03"
            if extended and ctx.request.research.historical_cases:
                return "B05"
            if extended and ctx.request.research.documents:
                return "F02"
            return "B03"
        if agent_id == "B05":
            return "F02" if ctx.request.research.documents else "B03"
        if agent_id == "B03":
            return "B06" if extended else "F03"
        return {
            "A06": "F03",
            "F02": "B03",
            "B06": "D02",
            "D02": "D06",
            "D06": "F03",
            "F03": "F04",
            "F04": None,
        }[agent_id]
