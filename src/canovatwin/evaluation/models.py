"""Versioned experiment contracts and leakage checks."""

import hashlib
import json
from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from ..contracts import Contract, FaultCode
from ..operating import ExperimentVariation, OperatingConditions
from ..telemetry import Scenario

Split = Literal["train", "validation", "test"]
Method = Literal["threshold", "core6", "mvp12"]
METHODS: tuple[Method, ...] = ("threshold", "core6", "mvp12")


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


class ExperimentCase(Contract):
    case_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    split: Split
    scenario: Scenario
    seed: int = Field(ge=0, le=2**32 - 1)
    count: int = Field(default=240, ge=60, le=600)
    start: AwareDatetime
    conditions: OperatingConditions = OperatingConditions()
    variation: ExperimentVariation = ExperimentVariation()


class ExperimentManifest(Contract):
    schema_version: Literal["1.0"] = "1.0"
    generator_version: Literal["evaluation-1.0"] = "evaluation-1.0"
    dataset_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    source: Literal["canovatwin-synthetic"] = "canovatwin-synthetic"
    license: Literal["MIT"] = "MIT"
    cases: tuple[ExperimentCase, ...] = Field(min_length=3, max_length=300)

    @model_validator(mode="after")
    def isolated_splits(self):
        identifiers, configurations = set(), set()
        seed_splits: dict[int, Split] = {}
        for case in self.cases:
            if case.case_id in identifiers:
                raise ValueError("case_id must be unique")
            identifiers.add(case.case_id)
            configuration = digest(case.model_dump(mode="json", exclude={"case_id", "split"}))
            if configuration in configurations:
                raise ValueError("Duplicate generated case configuration")
            configurations.add(configuration)
            if case.seed in seed_splits and seed_splits[case.seed] != case.split:
                raise ValueError("Seeds must not be shared across splits")
            seed_splits[case.seed] = case.split
        if {case.split for case in self.cases} != {"train", "validation", "test"}:
            raise ValueError("Manifest must declare train, validation and test splits")
        return self


class Prediction(Contract):
    status: Literal["clear", "needs_review", "insufficient_data", "blocked"]
    predicted: tuple[FaultCode, ...] = ()
    active_agents: int = Field(default=0, ge=0, le=36)
    verification_passed: bool | None = None
    model_mae_c: float | None = Field(default=None, ge=0)
    model_rmse_c: float | None = Field(default=None, ge=0)
    failure_code: str | None = None

    @model_validator(mode="after")
    def consistent_prediction(self):
        if len(set(self.predicted)) != len(self.predicted):
            raise ValueError("Predictions must not repeat a label")
        if FaultCode.COMBINED in self.predicted:
            raise ValueError("Combined faults must use their primitive labels")
        if (self.status == "blocked") != (self.failure_code is not None):
            raise ValueError("Blocked predictions require a failure code")
        if self.status in ("blocked", "clear") and self.predicted:
            raise ValueError("Blocked/clear predictions cannot carry fault candidates")
        return self


class CaseResult(Contract):
    case_id: str
    split: Split
    method: Method
    input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    truth: tuple[FaultCode, ...]
    prediction: Prediction
    elapsed_ms: float = Field(ge=0)


class ClassificationScore(Contract):
    tp: int
    fp: int
    fn: int
    precision: float | None
    recall: float | None
    f1: float | None


class MethodSummary(Contract):
    method: Method
    total: int
    scored: int
    blocked: int
    coverage: float
    insufficient_data: int
    alarm: ClassificationScore
    true_negatives: int
    false_alarm_rate: float | None
    labels: dict[FaultCode, ClassificationScore]
    macro_f1: float | None
    top3_fault_recall: float | None
    latency_p50_ms: float
    latency_p95_ms: float
    mean_active_agents: float
    verification_pass_rate: float | None
    model_cases: int
    mean_model_mae_c: float | None
    mean_model_rmse_c: float | None


class EvaluationReport(Contract):
    protocol_version: Literal["1.0"] = "1.0"
    engine_version: str
    implementation_sha256: str
    manifest_sha256: str
    result_sha256: str
    environment: dict[str, str]
    split: Split
    manifest: ExperimentManifest
    results: tuple[CaseResult, ...]
    summaries: tuple[MethodSummary, ...]
