"""Verify provenance and recompute numerical claims from original telemetry."""

from ..contracts import VerificationResult
from ..state import AnalysisContext
from .diagnosis import diagnose, investigate
from .quality import check_quality
from .research import analyze_missing_data, critique_hypotheses, match_history, retrieve_documents
from .signals import analyze_signals
from .simulation import design_simulation, validate_simulation


def verify(ctx: AnalysisContext) -> VerificationResult:
    errors = []
    expected_quality = check_quality(ctx)
    if ctx.quality != expected_quality:
        errors.append("Quality output disagrees with source telemetry")
    expected_evidence = list(expected_quality.evidence)
    if ctx.signals is not None:
        if not expected_quality.usable:
            errors.append("Signal analysis used invalid telemetry")
        else:
            expected_signals = analyze_signals(ctx)
            expected_evidence.extend(expected_signals.evidence)
            if ctx.signals != expected_signals:
                errors.append("Signal statistics disagree with source telemetry")
    if ctx.missing_data is not None:
        expected_missing = analyze_missing_data(ctx)
        expected_evidence.extend(expected_missing.evidence)
        if ctx.missing_data != expected_missing:
            errors.append("Missing data findings disagree with source telemetry")
    if ctx.history is not None:
        expected_history = match_history(ctx)
        expected_evidence.extend(expected_history.evidence)
        if ctx.history != expected_history:
            errors.append("Historical matches disagree with captured case snapshots")
    if ctx.retrieval is not None:
        expected_retrieval = retrieve_documents(ctx)
        expected_evidence.extend(expected_retrieval.evidence)
        if ctx.retrieval != expected_retrieval:
            errors.append("Document citations disagree with captured source text")
    if ctx.critique is not None and ctx.critique != critique_hypotheses(ctx):
        errors.append("Hypothesis review disagrees with candidate evidence")
    if ctx.simulation is not None:
        expected_simulation = design_simulation(ctx)
        expected_evidence.extend(expected_simulation.evidence)
        if ctx.simulation != expected_simulation:
            errors.append("What-if simulation differs from its recorded parameters")
    if ctx.simulation_validation is not None:
        expected_validation = validate_simulation(ctx)
        expected_evidence.extend(expected_validation.evidence)
        if ctx.simulation_validation != expected_validation:
            errors.append("Model validation differs from source predictions")
    if ctx.anomaly is not None:
        if ctx.signals is None:
            errors.append("Anomaly output lacks signal analysis")
        elif ctx.anomaly != investigate(ctx):
            errors.append("Anomaly claims disagree with signal rules")
    if ctx.diagnosis is not None:
        if ctx.anomaly is None or ctx.signals is None:
            errors.append("Diagnosis lacks upstream analysis")
        elif ctx.diagnosis != diagnose(ctx):
            errors.append("Hypotheses disagree with supporting or contradicting evidence")
    if tuple(expected_evidence) != ctx.evidence:
        errors.append("Evidence store contains missing, duplicate, altered or unproven records")
    known_ids = {e.evidence_id for e in ctx.evidence}
    references = []
    if ctx.quality:
        references.extend(ref for issue in ctx.quality.issues for ref in issue.evidence_ids)
    if ctx.anomaly:
        references.extend(ref for item in ctx.anomaly.observations for ref in item.evidence_ids)
    if ctx.diagnosis:
        references.extend(
            ref
            for item in ctx.diagnosis.hypotheses
            for ref in item.supporting_evidence + item.contradicting_evidence
        )
    if ctx.missing_data:
        references.extend(ref for item in ctx.missing_data.observations for ref in item.evidence_ids)
    if ctx.critique:
        references.extend(
            ref
            for item in ctx.critique.reviews
            for ref in item.supporting_evidence + item.contradicting_evidence
        )
    if any(ref not in known_ids for ref in references):
        errors.append("Claim references an unknown evidence ID")
    return VerificationResult(
        passed=not errors,
        checked_evidence_ids=tuple(e.evidence_id for e in ctx.evidence),
        errors=tuple(errors),
    )
