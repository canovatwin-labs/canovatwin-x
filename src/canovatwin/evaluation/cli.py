"""Offline experiment CLI with explicit split selection and non-overwriting exports."""

import argparse
import csv
import sys
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from ..operating import ExperimentVariation, OperatingConditions
from ..telemetry import Scenario
from .models import EvaluationReport, ExperimentCase, ExperimentManifest
from .runner import evaluate


def demo_manifest() -> ExperimentManifest:
    cases = []
    for group, split in enumerate(("train", "validation", "test"), start=1):
        for level in range(2):
            for scenario in Scenario:
                cases.append(
                    ExperimentCase(
                        case_id=f"case-{len(cases) + 1:03d}",
                        split=split,
                        scenario=scenario,
                        seed=group * 1000 + level,
                        start=datetime(2026, 10, 30, tzinfo=UTC),
                        conditions=OperatingConditions(
                            workload="steady" if level == 0 else "cyclic", ambient_c=26.0 + 8 * level
                        ),
                        variation=ExperimentVariation(
                            onset_fraction=0.2 + 0.5 * level,
                            severity=0.4 + 0.6 * level,
                            sensor_noise_c=0.03 + 0.15 * level,
                            missing_fraction=0.5 + 0.5 * level,
                        ),
                    )
                )
    return ExperimentManifest(dataset_id="synthetic-evaluation-v1", cases=tuple(cases))


def _number(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.4f}"


def render_markdown(report: EvaluationReport) -> str:
    lines = [
        "# CanovaTwin X — Synthetic evaluation",
        "",
        f"Dataset: `{report.manifest.dataset_id}` · split: `{report.split}` · protocol: `{report.protocol_version}`",
        f"Manifest SHA-256: `{report.manifest_sha256}`",
        f"Logical result SHA-256: `{report.result_sha256}`",
        "",
        "This is a synthetic comparison, not field validation. All methods receive the same telemetry; labels stay outside the predictor boundary.",
        "Blocked runs are listed but excluded from conditional classification scores; always read coverage alongside F1. Insufficient data is an alarm, not a blocked execution.",
        "Combined faults expand to fan-loss and cooling-loss labels. Macro F1 averages labels with ground-truth or predicted support; absent denominators are n/a.",
        "Top-3 is mean ground-truth coverage by the first three candidates in existing rule order, not calibrated probabilistic ranking. Timing is a local observation, not an SLA.",
        "",
    ]
    for summary in report.summaries:
        lines.extend(
            [
                f"## {summary.method}",
                "",
                f"- Total/scored/blocked: {summary.total}/{summary.scored}/{summary.blocked}; coverage: {_number(summary.coverage)}.",
                f"- Alarm precision / recall / F1: {_number(summary.alarm.precision)} / {_number(summary.alarm.recall)} / {_number(summary.alarm.f1)}.",
                f"- False-alarm rate: {_number(summary.false_alarm_rate)}; candidate macro F1: {_number(summary.macro_f1)}; Top-3 fault recall: {_number(summary.top3_fault_recall)}.",
                f"- Insufficient-data outcomes: {summary.insufficient_data}; mean completed roles: {_number(summary.mean_active_agents)}.",
                f"- Latency p50/p95 ms: {_number(summary.latency_p50_ms)} / {_number(summary.latency_p95_ms)}.",
                f"- Internal evidence gate pass rate: {_number(summary.verification_pass_rate)} (not independent evidence accuracy).",
                f"- Model cases: {summary.model_cases}; mean MAE/RMSE: {_number(summary.mean_model_mae_c)} / {_number(summary.mean_model_rmse_c)} °C.",
                "",
            ]
        )
    return "\n".join(lines)


def _csv_cell(value: object) -> object:
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def export_report(report: EvaluationReport, destination: Path) -> None:
    # Exclusive directory creation is the ownership boundary. Never replace an
    # existing run, including a previous partially written export.
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "manifest.json").write_text(report.manifest.model_dump_json(indent=2) + "\n")
    (destination / "report.json").write_text(report.model_dump_json(indent=2) + "\n")
    (destination / "summary.md").write_text(render_markdown(report))
    with (destination / "cases.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "case_id",
                "split",
                "method",
                "truth",
                "predicted",
                "status",
                "failure_code",
                "active_agents",
                "elapsed_ms",
                "input_sha256",
            ]
        )
        for row in report.results:
            writer.writerow(
                [
                    _csv_cell(value)
                    for value in (
                        row.case_id,
                        row.split,
                        row.method,
                        "|".join(row.truth),
                        "|".join(row.prediction.predicted),
                        row.prediction.status,
                        row.prediction.failure_code or "",
                        row.prediction.active_agents,
                        row.elapsed_ms,
                        row.input_sha256,
                    )
                ]
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    template = commands.add_parser("template", help="Write a seed-disjoint synthetic manifest")
    template.add_argument("--output", type=Path, required=True)
    run = commands.add_parser("run", help="Compare three deterministic methods; no LLM or device access")
    run.add_argument("manifest", type=Path)
    run.add_argument("--split", choices=("train", "validation", "test"), default="test")
    run.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "template":
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(demo_manifest().model_dump_json(indent=2) + "\n")
            print(f"Manifest written: {args.output}")
            return 0
        with args.manifest.open("rb") as stream:
            content = stream.read(2_000_001)
        if len(content) > 2_000_000:
            raise ValueError("Manifest exceeds 2 MB")
        manifest = ExperimentManifest.model_validate_json(content)
        if args.output_dir.exists():
            raise ValueError("Output directory already exists; choose a new run directory")
        report = evaluate(manifest, split=args.split)
        export_report(report, args.output_dir)
        blocked = sum(s.blocked for s in report.summaries)
        print(
            f"Evaluated {len(report.results)} method/case pairs; blocked={blocked}; results: {args.output_dir}"
        )
        return 1 if blocked else 0
    except ValidationError as exc:
        print(
            "Invalid manifest: " + "; ".join(e["msg"] for e in exc.errors(include_input=False)[:3]),
            file=sys.stderr,
        )
    except (OSError, ValueError) as exc:
        print(f"Experiment failed: {exc}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
