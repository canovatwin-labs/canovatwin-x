import csv
import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from canovatwin.contracts import AnalysisRequest, FaultCode
from canovatwin.evaluation import runner
from canovatwin.evaluation.cli import demo_manifest, export_report, main, render_markdown
from canovatwin.evaluation.metrics import percentile, summarize
from canovatwin.evaluation.models import (
    CaseResult,
    EvaluationReport,
    ExperimentManifest,
    Prediction,
)
from canovatwin.operating import (
    ExperimentVariation,
    GenerationMetadata,
    OperatingConditions,
    generate_experiment_case,
    generate_operating_case,
)
from canovatwin.telemetry import Scenario, generate_case

ROOT = Path(__file__).resolve().parents[2]
START = datetime(2026, 10, 30, tzinfo=UTC)


@pytest.fixture
def manifest():
    template = demo_manifest()
    cases = tuple(
        c.model_copy(update={"count": 90})
        for c in template.cases
        if c.scenario in (Scenario.NORMAL, Scenario.FAN_LOSS) and c.seed % 1000 == 0
    )
    return ExperimentManifest(dataset_id="small-test", cases=cases)


@pytest.fixture
def report(manifest):
    return runner.evaluate(manifest)


def row(truth=(), predicted=(), *, status="needs_review", method="threshold", elapsed=1.0):
    return CaseResult(
        case_id="case",
        split="test",
        method=method,
        input_sha256="0" * 64,
        truth=truth,
        prediction=Prediction(
            status=status, predicted=predicted, failure_code="TEST_FAILURE" if status == "blocked" else None
        ),
        elapsed_ms=elapsed,
    )


def test_hand_computed_confusion_and_partial_top3():
    fan, cooling = FaultCode.FAN_LOSS, FaultCode.COOLING_LOSS
    rows = (
        row((fan,), (fan,)),
        row((fan, cooling), (fan,)),
        row((), (fan,)),
        row((), (), status="clear"),
        row((cooling,), (), status="clear"),
        row((fan,), (), status="blocked"),
    )
    summary = summarize("threshold", rows)
    assert (summary.total, summary.scored, summary.blocked) == (6, 5, 1)
    assert summary.coverage == 5 / 6
    assert (summary.alarm.tp, summary.alarm.fp, summary.alarm.fn, summary.true_negatives) == (2, 1, 1, 1)
    assert summary.alarm.precision == summary.alarm.recall == summary.alarm.f1 == 2 / 3
    assert summary.false_alarm_rate == 0.5
    assert summary.labels[fan].f1 == 0.8
    assert summary.labels[cooling].f1 == 0
    assert summary.macro_f1 == 0.4
    assert summary.top3_fault_recall == 0.5


def test_empty_denominators_are_null_and_all_blocked_runs_stay_visible():
    summary = summarize("threshold", (row(status="blocked"),))
    assert summary.scored == 0 and summary.blocked == 1 and summary.coverage == 0
    assert summary.alarm.f1 is None and summary.false_alarm_rate is None
    assert summary.macro_f1 is None and summary.top3_fault_recall is None
    assert summary.verification_pass_rate is None and summary.model_cases == 0
    with pytest.raises(ValueError, match="empty method"):
        summarize("core6", (row(),))


def test_normal_only_scores_do_not_invent_recall():
    summary = summarize("threshold", (row(status="clear"),))
    assert summary.alarm.recall is None and summary.false_alarm_rate == 0
    assert percentile([10.0, 20.0, 30.0], 0.5) == 20
    assert percentile([10.0, 20.0, 30.0], 0.95) == 29


@pytest.mark.parametrize(
    "mutation,match",
    [
        ("seed", "Seeds"),
        ("id", "case_id"),
        ("duplicate", "Duplicate"),
        ("split", "splits"),
    ],
)
def test_manifest_rejects_split_leakage_and_duplicates(manifest, mutation, match):
    data = manifest.model_dump(mode="json")
    if mutation == "seed":
        data["cases"][2]["seed"] = data["cases"][0]["seed"]
        data["cases"][2]["variation"]["severity"] = 0.7
    elif mutation == "id":
        data["cases"][1]["case_id"] = data["cases"][0]["case_id"]
    elif mutation == "duplicate":
        data["cases"].append({**data["cases"][0], "case_id": "another"})
    else:
        data["cases"] = [c for c in data["cases"] if c["split"] != "test"]
    with pytest.raises(ValidationError, match=match):
        ExperimentManifest.model_validate_json(json.dumps(data))


@pytest.mark.parametrize(
    "field,value",
    [
        ("severity", float("nan")),
        ("onset_fraction", 0.99),
        ("missing_fraction", 0.0),
        ("sensor_noise_c", -1.0),
    ],
)
def test_variation_rejects_invalid_parameters(field, value):
    with pytest.raises(ValidationError):
        ExperimentVariation.model_validate({field: value})


def test_manifest_rejects_unknown_source_and_bypassed_validation(manifest):
    with pytest.raises(ValidationError):
        ExperimentManifest.model_validate_json(
            manifest.model_dump_json().replace("canovatwin-synthetic", "plc")
        )
    with pytest.raises(ValidationError):
        runner.evaluate(manifest.model_copy(update={"cases": ()}))
    with pytest.raises(ValueError, match="Unknown split"):
        runner.evaluate(manifest, split="all")


def test_predictor_receives_only_telemetry_and_failure_does_not_disappear(manifest, monkeypatch):
    seen = []

    def spy(method, request):
        assert isinstance(request, AnalysisRequest)
        assert request.research is None
        assert set(request.model_dump()) == {"schema_version", "window", "as_of", "clock_mode", "research"}
        assert set(request.window.model_dump()) == {"source", "asset_id", "samples"}
        seen.append(request.model_dump_json())
        return (
            Prediction(status="blocked", failure_code="TEST_FAILURE")
            if method == "mvp12"
            else Prediction(status="clear")
        )

    monkeypatch.setattr(runner, "predict", spy)
    report = runner.evaluate(manifest)
    assert len(report.results) == 6
    assert len(set(seen)) == 2
    assert all(row.split == "test" for row in report.results)
    assert report.summaries[2].blocked == 2 and report.summaries[2].coverage == 0


def test_duplicate_content_is_rejected_before_any_predictor_runs(manifest, monkeypatch):
    case = generate_case(start=START)
    monkeypatch.setattr(runner, "generate_experiment_case", lambda *_: case)

    def never(*_):
        pytest.fail("Predictor ran before dataset leakage validation")

    monkeypatch.setattr(runner, "predict", never)
    with pytest.raises(ValueError, match="Duplicate telemetry"):
        runner.evaluate(manifest)


def test_fingerprint_ignores_renamed_samples_and_absolute_time():
    a = generate_case(start=START)
    b = generate_case(start=START + timedelta(days=1))
    assert runner._content_fingerprint(a) == runner._content_fingerprint(b)


def test_repeatable_results_valid_export_and_no_overwrite(report, manifest, tmp_path):
    second = runner.evaluate(manifest)
    assert report.result_sha256 == second.result_sha256
    assert report.manifest_sha256 == second.manifest_sha256
    assert report.implementation_sha256 == second.implementation_sha256
    assert len({r.input_sha256 for r in report.results}) == 2
    output = tmp_path / "run"
    export_report(report, output)
    assert EvaluationReport.model_validate_json((output / "report.json").read_text()) == report
    assert ExperimentManifest.model_validate_json((output / "manifest.json").read_text()) == manifest
    with (output / "cases.csv").open() as stream:
        assert len(list(csv.DictReader(stream))) == 6
    assert "not field validation" in render_markdown(report)
    with pytest.raises(FileExistsError):
        export_report(second, output)
    assert EvaluationReport.model_validate_json((output / "report.json").read_text()) == report


def test_cli_template_run_and_input_errors(manifest, tmp_path, capsys):
    template = tmp_path / "template.json"
    assert main(["template", "--output", str(template)]) == 0
    assert len(ExperimentManifest.model_validate_json(template.read_text()).cases) == 66
    assert main(["template", "--output", str(template)]) == 2
    template.write_text(manifest.model_dump_json())
    output = tmp_path / "results"
    assert main(["run", str(template), "--output-dir", str(output)]) == 0
    assert main(["run", str(template), "--output-dir", str(output)]) == 2
    template.write_text("{}")
    assert main(["run", str(template), "--output-dir", str(tmp_path / "invalid")]) == 2
    assert "Invalid manifest" in capsys.readouterr().err
    template.write_bytes(b"x" * 2_000_001)
    assert main(["run", str(template), "--output-dir", str(tmp_path / "large")]) == 2
    assert not (tmp_path / "large").exists()


def test_cli_returns_nonzero_for_blocked_report_and_escapes_csv(report, tmp_path, monkeypatch):
    from canovatwin.evaluation import cli

    blocked = tuple(
        r.model_copy(
            update={"case_id": "-2", "prediction": Prediction(status="blocked", failure_code="FAILED")}
        )
        for r in report.results
    )
    bad = report.model_copy(
        update={
            "results": blocked,
            "summaries": tuple(summarize(method, blocked) for method in ("threshold", "core6", "mvp12")),
        }
    )
    monkeypatch.setattr(cli, "evaluate", lambda *a, **kw: bad)
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text(report.manifest.model_dump_json())
    assert main(["run", str(manifest_file), "--output-dir", str(tmp_path / "run")]) == 1
    assert "'-2" in (tmp_path / "run/cases.csv").read_text()


@pytest.mark.parametrize("scenario", list(Scenario))
@pytest.mark.parametrize("workload", ["steady", "cyclic", "batch"])
def test_dynamic_v1_outputs_match_pre_sprint7_release(scenario, workload):
    frozen = json.loads((ROOT / "tests/fixtures/dynamic_v1_checksums.json").read_text())
    case = generate_operating_case(
        GenerationMetadata(
            scenario=scenario,
            count=120,
            seed=42,
            start=START,
            conditions=OperatingConditions(workload=workload),
        )
    )

    # libm can differ in its last bits across macOS/Linux. Compare the entire
    # series at 0.001-unit resolution, then hash canonical JSON. Raw macOS
    # hashes remain in the fixture as provenance, not as a portable test oracle.
    def quantize(value):
        if isinstance(value, float):
            return round(value, frozen["portable_precision_digits"])
        if isinstance(value, list):
            return [quantize(item) for item in value]
        if isinstance(value, dict):
            return {key: quantize(item) for key, item in value.items()}
        return value

    canonical = json.dumps(
        quantize(case.window.model_dump(mode="json")), sort_keys=True, separators=(",", ":")
    )
    assert (
        hashlib.sha256(canonical.encode()).hexdigest()
        == frozen["portable_checksums"][scenario.value + "/" + workload]
    )


def test_variation_changes_onset_strength_noise_and_missing_rate():
    def case(scenario, **changes):
        return generate_experiment_case(
            GenerationMetadata(
                scenario=scenario, count=240, seed=42, start=START, conditions=OperatingConditions()
            ),
            ExperimentVariation(**changes),
        )

    early = case(Scenario.SENSOR_BIAS, onset_fraction=0.2, severity=0.25, sensor_noise_c=0.0)
    late = case(Scenario.SENSOR_BIAS, onset_fraction=0.7, severity=1.0, sensor_noise_c=0.0)
    assert (early.fault_started_at - START).total_seconds() == 48
    assert (late.fault_started_at - START).total_seconds() == 168
    assert late.window.samples[-1].inlet_c - early.window.samples[-1].inlet_c == pytest.approx(3.75)
    sparse = case(Scenario.SENSOR_MISSING, missing_fraction=0.2)
    missing = case(Scenario.SENSOR_MISSING, missing_fraction=1.0)
    assert sum(s.inlet_c is None for s in sparse.window.samples) < sum(
        s.inlet_c is None for s in missing.window.samples
    )
    assert [s.it_load_kw for s in sparse.window.samples] == [s.it_load_kw for s in missing.window.samples]
    noisy = case(Scenario.NORMAL, sensor_noise_c=0.5)
    quiet = case(Scenario.NORMAL, sensor_noise_c=0.0)
    assert noisy.window != quiet.window
    assert [s.reference_inlet_c for s in noisy.window.samples] == [
        s.reference_inlet_c for s in quiet.window.samples
    ]


@pytest.mark.parametrize("scenario", list(Scenario))
def test_all_methods_on_all_scenarios_have_valid_bounded_results(scenario):
    case = generate_case(scenario, start=START)
    request = AnalysisRequest(window=case.window, as_of=case.observation_time)
    for method in ("threshold", "core6", "mvp12"):
        prediction = runner.predict(method, request)
        assert prediction.status != "blocked"
        assert prediction.active_agents <= 12
    with pytest.raises(ValueError, match="Unknown method"):
        runner.predict("unknown", request)


def test_full_demo_combined_truth_and_model_metrics():
    report = runner.evaluate(demo_manifest())
    assert len(report.results) == 66
    assert any(len(r.truth) == 2 for r in report.results)
    assert all(FaultCode.COMBINED not in r.truth for r in report.results)
    assert report.summaries[2].model_cases > 0
    assert report.summaries[2].verification_pass_rate == 1


def test_blocked_supervisor_prediction_is_not_reported_as_success(monkeypatch):
    from canovatwin.policy import default_policy
    from canovatwin.supervisor import Supervisor

    case = generate_case(Scenario.FAN_LOSS, start=START)
    request = AnalysisRequest(window=case.window, as_of=case.observation_time)
    broken = Supervisor(default_policy(request).model_copy(update={"max_agents": 1})).run(request)
    assert broken.status == "blocked"
    monkeypatch.setattr(runner.Supervisor, "run", lambda self, request: broken)
    prediction = runner.predict("core6", request)
    assert prediction.status == "blocked" and prediction.verification_passed is False


@pytest.mark.parametrize(
    "kwargs",
    [
        {"status": "blocked"},
        {"status": "clear", "failure_code": "error"},
        {"status": "clear", "predicted": (FaultCode.FAN_LOSS,)},
        {"status": "needs_review", "predicted": (FaultCode.COMBINED,)},
        {"status": "needs_review", "predicted": (FaultCode.FAN_LOSS, FaultCode.FAN_LOSS)},
    ],
)
def test_prediction_rejects_inconsistent_outcomes(kwargs):
    with pytest.raises(ValidationError):
        Prediction(**kwargs)
