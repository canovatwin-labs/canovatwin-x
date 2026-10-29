"""Immutable per-task state; no process-global incident memory."""

from dataclasses import dataclass

from .contracts import (
    AnalysisRequest,
    AnomalyResult,
    CritiqueResult,
    DiagnosisResult,
    Evidence,
    HistoricalResult,
    MissingDataResult,
    QualityResult,
    RetrievalResult,
    SignalResult,
    SimulationResult,
    SimulationValidationResult,
    VerificationResult,
)
from .policy import Policy


@dataclass(frozen=True)
class AnalysisContext:
    incident_id: str
    request: AnalysisRequest
    policy: Policy
    evidence: tuple[Evidence, ...] = ()
    quality: QualityResult | None = None
    signals: SignalResult | None = None
    anomaly: AnomalyResult | None = None
    diagnosis: DiagnosisResult | None = None
    verification: VerificationResult | None = None
    missing_data: MissingDataResult | None = None
    history: HistoricalResult | None = None
    retrieval: RetrievalResult | None = None
    critique: CritiqueResult | None = None
    simulation: SimulationResult | None = None
    simulation_validation: SimulationValidationResult | None = None
