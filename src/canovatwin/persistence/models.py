"""Immutable history records; lifecycle state is distinct from diagnostic outcome."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AwareDatetime, Field, StringConstraints, field_validator, model_validator

from ..contracts import AnalysisRequest, AnalysisRun, Contract, Identifier, VerificationResult
from ..identity import incident_identifier
from ..operating import GenerationMetadata
from ..policy import Policy
from ..stream_experiment import StreamExperiment

Actor = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Reason = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class IncidentStatus(StrEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    CLOSED = "closed"


class RecordedAnalysis(Contract):
    schema_version: Literal["1.0"] = "1.0"
    run_id: Identifier
    recorded_at: AwareDatetime
    actor: Actor
    engine_version: Annotated[str, StringConstraints(min_length=1, max_length=50)]
    request: AnalysisRequest
    policy: Policy
    result: AnalysisRun
    replay_of: Identifier | None = None
    generation: GenerationMetadata | None = None
    stream_experiment: StreamExperiment | None = None

    @field_validator("recorded_at")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def coherent_identity(self):
        if self.stream_experiment is not None:
            if self.generation is not None:
                raise ValueError("Stream generation belongs inside its transport recipe")
            if (
                self.stream_experiment.window != self.request.window
                or self.stream_experiment.as_of != self.request.as_of
            ):
                raise ValueError("Stream experiment does not match the analyzed window and clock")
        expected = incident_identifier(self.request, self.policy)
        if self.result.incident_id != expected:
            raise ValueError("Result does not belong to the recorded request and policy")
        if self.result.clock_mode != self.request.clock_mode:
            raise ValueError("Clock mode does not match the request")
        if any(output.incident_id != expected for output in self.result.outputs):
            raise ValueError("Agent output belongs to a different incident")
        if self.result.report and self.result.report.incident_id != expected:
            raise ValueError("Report belongs to a different incident")
        if self.result.total_tool_calls != sum(step.tool_calls for step in self.result.trace):
            raise ValueError("Tool totals disagree with the execution trace")
        if self.result.status == "completed":
            outputs = self.result.outputs
            if not outputs or outputs[-1].agent_id != "F04" or outputs[-1].payload != self.result.report:
                raise ValueError("Final report does not match its composer output")
            verifications = [
                output.payload
                for output in outputs
                if output.agent_id == "F03" and isinstance(output.payload, VerificationResult)
            ]
            evidence_ids = tuple(e.evidence_id for e in self.result.evidence)
            if (
                len(verifications) != 1
                or not verifications[0].passed
                or verifications[0].checked_evidence_ids != evidence_ids
                or self.result.report.evidence_ids != evidence_ids
                or any(step.status != "completed" for step in self.result.trace)
            ):
                raise ValueError("Completed history requires coherent verification and execution evidence")
        if self.replay_of == self.run_id:
            raise ValueError("A run cannot replay itself")
        return self


class Transition(Contract):
    incident_id: Identifier
    target: IncidentStatus
    expected_revision: int = Field(ge=1)
    actor: Actor
    reason: Reason


class IncidentSummary(Contract):
    incident_id: Identifier
    asset_id: Identifier
    status: IncidentStatus
    revision: int = Field(ge=1)
    created_at: AwareDatetime
    updated_at: AwareDatetime
    run_count: int = Field(ge=1)
    latest_run_id: Identifier
    latest_analysis_status: Literal["completed", "blocked"]
    latest_report_status: Literal["clear", "needs_review", "insufficient_data"] | None


class RunSummary(Contract):
    run_id: Identifier
    incident_id: Identifier
    recorded_at: AwareDatetime
    engine_version: str
    status: Literal["completed", "blocked"]
    report_status: Literal["clear", "needs_review", "insufficient_data"] | None
    replay_of: Identifier | None


class AuditEvent(Contract):
    event_id: int = Field(ge=1)
    incident_id: Identifier
    run_id: Identifier | None
    recorded_at: AwareDatetime
    actor: Actor
    action: Literal["incident_created", "analysis_saved", "status_changed"]
    old_status: IncidentStatus | None
    new_status: IncidentStatus | None
    reason: str
    revision: int = Field(ge=1)


class ReplayOutcome(Contract):
    record: RecordedAnalysis
    matches: bool
    differences: tuple[str, ...]
