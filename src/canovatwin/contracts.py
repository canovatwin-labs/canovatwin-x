"""Versioned, immutable boundaries shared by all six specialists."""

from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

AgentId = Annotated[str, Field(pattern=r"^[A-F]0[1-6]$")]
Identifier = Annotated[str, Field(min_length=1, max_length=100)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, allow_inf_nan=False)


class FaultCode(StrEnum):
    FAN_LOSS = "FAULT_F01"
    SENSOR_BIAS = "FAULT_F02"
    SENSOR_MISSING = "FAULT_F03"
    LOAD_SURGE = "FAULT_F04"
    COOLING_LOSS = "FAULT_F05"
    AIRFLOW_RESTRICTION = "FAULT_F06"
    FAN_MISMATCH = "FAULT_F07"
    COMMUNICATION_LOSS = "FAULT_F08"
    CONTROL_OSCILLATION = "FAULT_F09"
    COMBINED = "FAULT_F10"


class SensorSample(Contract):
    sample_id: Identifier
    timestamp: datetime
    # None is an explicit missing observation, never silently imputed.
    inlet_c: float | None
    reference_inlet_c: float | None
    return_c: float | None
    supply_c: float | None
    ambient_c: float | None
    humidity_pct: float | None
    fan_command_pct: float | None
    fan_feedback_pct: float | None
    airflow_m3s: float | None
    it_load_kw: float | None
    cooling_kw: float | None

    @model_validator(mode="after")
    def timezone_required(self):
        if self.timestamp.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        return self


class TelemetryWindow(Contract):
    source: Literal["synthetic"] = "synthetic"
    asset_id: Identifier = "synthetic-unit-01"
    samples: tuple[SensorSample, ...] = Field(min_length=3, max_length=600)


class TechnicalDocument(Contract):
    document_id: Identifier
    title: str = Field(min_length=1, max_length=200)
    version: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1, max_length=12000)
    source_kind: Literal["demo_reference", "user_supplied"] = "user_supplied"
    content_hash: str = Field(default="", pattern=r"^$|^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def verify_hash(self):
        expected = sha256(self.content.encode()).hexdigest()
        if self.content_hash and self.content_hash != expected:
            raise ValueError("Document content hash mismatch")
        object.__setattr__(self, "content_hash", expected)
        return self


class HistoricalCase(Contract):
    run_id: Identifier
    incident_id: Identifier
    asset_id: Identifier
    window_start: AwareDatetime
    window_end: AwareDatetime
    engine_version: str = Field(min_length=1, max_length=50)
    observation_codes: tuple[Identifier, ...] = Field(max_length=30)
    candidate_faults: tuple[FaultCode, ...] = Field(max_length=10)
    assessment: Literal["unconfirmed"] = "unconfirmed"

    @model_validator(mode="after")
    def ordered_window(self):
        if self.window_end < self.window_start:
            raise ValueError("Historical window is reversed")
        return self


class SimulationParameters(Contract):
    thermal_capacity_kj_per_k: float = Field(default=120.0, ge=10, le=100000)
    ambient_conductance_kw_per_k: float = Field(default=0.1, ge=0, le=10)
    horizon_s: int = Field(default=60, ge=10, le=120)
    max_mae_c: float = Field(default=0.5, gt=0, le=10)
    max_rmse_c: float = Field(default=0.75, gt=0, le=10)


class ResearchInputs(Contract):
    profile: Literal["mvp12"] = "mvp12"
    documents: tuple[TechnicalDocument, ...] = Field(default=(), max_length=8)
    historical_cases: tuple[HistoricalCase, ...] = Field(default=(), max_length=20)
    simulation: SimulationParameters = SimulationParameters()
    expected_interval_s: float = Field(default=1.0, ge=0.1, le=60)

    @model_validator(mode="after")
    def unique_sources(self):
        if len({d.document_id for d in self.documents}) != len(self.documents):
            raise ValueError("Document IDs must be unique")
        if len({c.run_id for c in self.historical_cases}) != len(self.historical_cases):
            raise ValueError("Historical run IDs must be unique")
        return self


class AnalysisRequest(Contract):
    schema_version: Literal["1.0"] = "1.0"
    window: TelemetryWindow
    as_of: datetime
    clock_mode: Literal["replay", "realtime"] = "replay"
    research: ResearchInputs | None = None

    @model_validator(mode="after")
    def timezone_required(self):
        if self.as_of.utcoffset() is None:
            raise ValueError("as_of must include a timezone")
        return self


class Evidence(Contract):
    evidence_id: Identifier
    producer: AgentId
    metric: Identifier
    value: float
    unit: str
    sample_ids: tuple[Identifier, ...] = Field(min_length=1, max_length=600)
    source: Literal["synthetic", "historical_snapshot", "document_snapshot", "simulation"] = "synthetic"


class Observation(Contract):
    code: Identifier
    message: str
    evidence_ids: tuple[Identifier, ...] = Field(min_length=1)


class Hypothesis(Contract):
    fault_code: FaultCode
    explanation: str
    supporting_evidence: tuple[Identifier, ...] = Field(min_length=1)
    contradicting_evidence: tuple[Identifier, ...] = ()
    assessment: Literal["candidate", "uncertain"] = "candidate"


class QualityResult(Contract):
    kind: Literal["quality"] = "quality"
    usable: bool
    issues: tuple[Observation, ...]
    evidence: tuple[Evidence, ...]


class SignalResult(Contract):
    kind: Literal["signals"] = "signals"
    evidence: tuple[Evidence, ...]


class AnomalyResult(Contract):
    kind: Literal["anomaly"] = "anomaly"
    detected: bool
    observations: tuple[Observation, ...]


class DiagnosisResult(Contract):
    kind: Literal["diagnosis"] = "diagnosis"
    hypotheses: tuple[Hypothesis, ...]


class MissingField(Contract):
    sensor: Identifier
    missing_count: int = Field(ge=1, le=600)
    longest_missing_s: float = Field(ge=0)


class MissingDataResult(Contract):
    kind: Literal["missing_data"] = "missing_data"
    fields: tuple[MissingField, ...]
    estimated_lost_samples: int = Field(ge=0)
    stale_stream: bool
    observations: tuple[Observation, ...]
    evidence: tuple[Evidence, ...]
    limitation: str


class HistoricalMatch(Contract):
    run_id: Identifier
    score: float = Field(gt=0, le=1)
    shared_observations: tuple[Identifier, ...]
    candidate_faults: tuple[FaultCode, ...]
    assessment: Literal["unconfirmed"] = "unconfirmed"


class HistoricalResult(Contract):
    kind: Literal["history"] = "history"
    matches: tuple[HistoricalMatch, ...] = Field(max_length=3)
    excluded_count: int = Field(ge=0)
    evidence: tuple[Evidence, ...]


class DocumentHit(Contract):
    document_id: Identifier
    title: str
    version: str
    content_hash: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    excerpt: str = Field(min_length=1, max_length=600)
    score: float = Field(gt=0, le=1)
    matched_terms: tuple[str, ...]


class RetrievalResult(Contract):
    kind: Literal["retrieval"] = "retrieval"
    hits: tuple[DocumentHit, ...] = Field(max_length=3)
    evidence: tuple[Evidence, ...]
    method: Literal["lexical_snapshot_search"] = "lexical_snapshot_search"


class HypothesisReview(Contract):
    fault_code: FaultCode
    verdict: Literal["retained", "weak", "inconclusive"]
    reason: str
    supporting_evidence: tuple[Identifier, ...]
    contradicting_evidence: tuple[Identifier, ...]
    historical_refs: tuple[Identifier, ...]
    document_refs: tuple[Identifier, ...]


class CritiqueResult(Contract):
    kind: Literal["critique"] = "critique"
    reviews: tuple[HypothesisReview, ...]


class SimulationCase(Contract):
    scenario_id: Identifier
    fault_codes: tuple[FaultCode, ...]
    load_kw: float = Field(ge=0)
    cooling_kw: float = Field(ge=0)
    final_c: float
    reduction_vs_baseline_c: float


class SimulationResult(Contract):
    kind: Literal["simulation"] = "simulation"
    predicted_reference_c: tuple[float, ...] = Field(min_length=3, max_length=600)
    baseline_final_c: float
    cases: tuple[SimulationCase, ...] = Field(max_length=4)
    evidence: tuple[Evidence, ...]
    limitation: str


class SimulationAssessment(Contract):
    scenario_id: Identifier
    assessment: Literal["illustrative_only", "reduction_in_model", "no_material_reduction"]


class SimulationValidationResult(Contract):
    kind: Literal["simulation_validation"] = "simulation_validation"
    mae_c: float = Field(ge=0)
    rmse_c: float = Field(ge=0)
    model_adequate: bool
    assessments: tuple[SimulationAssessment, ...]
    evidence: tuple[Evidence, ...]


class ResearchSummary(Contract):
    missing_fields: tuple[MissingField, ...] = ()
    stale_stream: bool = False
    historical_matches: tuple[HistoricalMatch, ...] = ()
    document_hits: tuple[DocumentHit, ...] = ()
    hypothesis_reviews: tuple[HypothesisReview, ...] = ()
    simulation_cases: tuple[SimulationCase, ...] = ()
    model_adequate: bool | None = None
    model_mae_c: float | None = None
    model_rmse_c: float | None = None


class VerificationResult(Contract):
    kind: Literal["verification"] = "verification"
    passed: bool
    checked_evidence_ids: tuple[Identifier, ...]
    errors: tuple[str, ...]


class TechnicalReport(Contract):
    kind: Literal["report"] = "report"
    schema_version: Literal["1.0"] = "1.0"
    incident_id: Identifier
    status: Literal["clear", "needs_review", "insufficient_data"]
    summary: str
    observations: tuple[Observation, ...]
    hypotheses: tuple[Hypothesis, ...]
    evidence_ids: tuple[Identifier, ...]
    limitations: tuple[str, ...]
    human_review_required: bool
    research: ResearchSummary | None = None


AgentPayload = Annotated[
    QualityResult
    | SignalResult
    | AnomalyResult
    | DiagnosisResult
    | VerificationResult
    | TechnicalReport
    | MissingDataResult
    | HistoricalResult
    | RetrievalResult
    | CritiqueResult
    | SimulationResult
    | SimulationValidationResult,
    Field(discriminator="kind"),
]


class AgentOutput(Contract):
    schema_version: Literal["1.0"] = "1.0"
    agent_id: AgentId
    task_id: Identifier
    incident_id: Identifier
    payload: AgentPayload


class AgentRun(Contract):
    agent_id: AgentId
    task_id: Identifier
    status: Literal["completed", "failed"]
    tool_calls: int = Field(ge=0)
    elapsed_ms: float = Field(ge=0)
    error_code: str | None = None


class RunFailure(Contract):
    code: str
    message: str


class AnalysisRun(Contract):
    schema_version: Literal["1.0"] = "1.0"
    incident_id: Identifier
    mode: Literal["simulation"] = "simulation"
    clock_mode: Literal["replay", "realtime"]
    status: Literal["completed", "blocked"]
    report: TechnicalReport | None
    outputs: tuple[AgentOutput, ...]
    trace: tuple[AgentRun, ...]
    evidence: tuple[Evidence, ...]
    failure: RunFailure | None = None
    total_tool_calls: int = Field(ge=0)
    llm_calls: Literal[0] = 0
    commands: tuple[()] = ()

    @model_validator(mode="after")
    def consistent_outcome(self):
        if self.status == "completed" and (self.report is None or self.failure is not None):
            raise ValueError("Completed runs require a report and no failure")
        if self.status == "blocked" and (self.report is not None or self.failure is None):
            raise ValueError("Blocked runs require a failure and no report")
        return self
