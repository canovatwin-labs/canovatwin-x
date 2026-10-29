"""Prepare all splits, enforce isolation, then evaluate only the requested split."""

import hashlib
import platform
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

from ..contracts import AnalysisRequest, FaultCode, ResearchInputs
from ..knowledge import demo_documents
from ..operating import GenerationMetadata, generate_experiment_case
from ..supervisor import Supervisor
from ..telemetry import ScenarioCase
from ..version import ENGINE_VERSION
from .baseline import predict_threshold
from .metrics import summarize
from .models import (
    METHODS,
    CaseResult,
    EvaluationReport,
    ExperimentManifest,
    Method,
    Prediction,
    Split,
    digest,
)


def _source_digest() -> str:
    root = Path(__file__).resolve().parents[1]
    hasher = hashlib.sha256()
    for file in sorted(root.rglob("*.py")):
        hasher.update(str(file.relative_to(root)).encode() + b"\0" + file.read_bytes())
    return hasher.hexdigest()


def _content_fingerprint(case: ScenarioCase) -> str:
    first = case.window.samples[0].timestamp
    values = [
        {
            **s.model_dump(mode="json", exclude={"sample_id", "timestamp"}),
            "relative_s": (s.timestamp - first).total_seconds(),
        }
        for s in case.window.samples
    ]
    return digest({"samples": values, "as_of_s": (case.observation_time - first).total_seconds()})


def predict(method: Method, request: AnalysisRequest) -> Prediction:
    # This boundary accepts telemetry, never ExperimentCase or ground truth.
    if method == "threshold":
        return predict_threshold(request)
    if method not in ("core6", "mvp12"):
        raise ValueError("Unknown method")
    research = ResearchInputs(documents=demo_documents()) if method == "mvp12" else None
    run = Supervisor().run(AnalysisRequest(window=request.window, as_of=request.as_of, research=research))
    active = sum(item.status == "completed" for item in run.trace)
    if run.status == "blocked":
        return Prediction(
            status="blocked", active_agents=active, verification_passed=False, failure_code=run.failure.code
        )
    report = run.report
    model = report.research
    return Prediction(
        status=report.status,
        predicted=tuple(h.fault_code for h in report.hypotheses),
        active_agents=active,
        verification_passed=True,
        model_mae_c=model.model_mae_c if model else None,
        model_rmse_c=model.model_rmse_c if model else None,
    )


def evaluate(manifest: ExperimentManifest, *, split: Split = "test") -> EvaluationReport:
    manifest = ExperimentManifest.model_validate(manifest.model_dump())
    if split not in ("train", "validation", "test"):
        raise ValueError("Unknown split")
    prepared, fingerprints = [], set()
    for specification in manifest.cases:
        metadata = GenerationMetadata(
            scenario=specification.scenario,
            count=specification.count,
            seed=specification.seed,
            start=specification.start,
            conditions=specification.conditions,
        )
        case = generate_experiment_case(metadata, specification.variation)
        fingerprint = _content_fingerprint(case)
        if fingerprint in fingerprints:
            raise ValueError("Duplicate telemetry content; changing IDs/timestamps does not isolate data")
        fingerprints.add(fingerprint)
        if specification.split == split:
            prepared.append((specification.case_id, case))
    rows = []
    for case_id, case in prepared:
        request = AnalysisRequest(window=case.window, as_of=case.observation_time)
        truth = (
            (FaultCode.FAN_LOSS, FaultCode.COOLING_LOSS)
            if case.fault_labels == (FaultCode.COMBINED,)
            else case.fault_labels
        )
        for method in METHODS:
            started = perf_counter()
            prediction = predict(method, request)
            rows.append(
                CaseResult(
                    case_id=case_id,
                    split=split,
                    method=method,
                    input_sha256=digest(request.model_dump(mode="json")),
                    truth=truth,
                    prediction=prediction,
                    elapsed_ms=(perf_counter() - started) * 1000,
                )
            )
    logical = [row.model_dump(mode="json", exclude={"elapsed_ms"}) for row in rows]
    return EvaluationReport(
        engine_version=ENGINE_VERSION,
        implementation_sha256=_source_digest(),
        manifest_sha256=digest(manifest.model_dump(mode="json")),
        result_sha256=digest(logical),
        environment={"python": platform.python_version(), "pydantic": version("pydantic")},
        split=split,
        manifest=manifest,
        results=tuple(rows),
        summaries=tuple(summarize(method, tuple(rows)) for method in METHODS),
    )
