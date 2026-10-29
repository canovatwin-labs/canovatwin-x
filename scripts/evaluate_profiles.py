"""Local smoke comparison of core6 and mvp12; not an academic accuracy benchmark."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from statistics import median, quantiles
from time import perf_counter

from canovatwin.contracts import AnalysisRequest, ResearchInputs
from canovatwin.knowledge import demo_documents
from canovatwin.supervisor import Supervisor
from canovatwin.telemetry import Scenario, generate_case


def evaluate(repeats: int = 3) -> dict:
    if not 1 <= repeats <= 10:
        raise ValueError("repeats must be 1–10")
    rows = []
    for profile in ("core6", "mvp12"):
        for scenario in Scenario:
            case = generate_case(scenario, start=datetime(2026, 10, 28, tzinfo=UTC))
            research = ResearchInputs(documents=demo_documents()) if profile == "mvp12" else None
            request = AnalysisRequest(window=case.window, as_of=case.observation_time, research=research)
            latencies = []
            reports = []
            for _ in range(repeats):
                start = perf_counter()
                run = Supervisor().run(request)
                latencies.append((perf_counter() - start) * 1000)
                if run.status != "completed":
                    raise RuntimeError(f"{profile}/{scenario}: {run.failure.code}")
                reports.append(run.report)
            assert all(report == reports[0] for report in reports)
            summary = run.report.research
            rows.append(
                dict(
                    profile=profile,
                    scenario=scenario.value,
                    report_status=run.report.status,
                    agent_count=len(run.trace),
                    tool_calls=run.total_tool_calls,
                    latency_p50_ms=median(latencies),
                    latency_p95_ms=quantiles(latencies, n=20, method="inclusive")[18]
                    if repeats > 1
                    else latencies[0],
                    final_candidates=[h.fault_code.value for h in run.report.hypotheses],
                    weak_candidates=sum(review.verdict == "weak" for review in summary.hypothesis_reviews)
                    if summary
                    else 0,
                    model_mae_c=summary.model_mae_c if summary else None,
                    model_rmse_c=summary.model_rmse_c if summary else None,
                )
            )
    return dict(
        engine_version="0.4.0",
        repeats=repeats,
        analysis_count=len(rows) * repeats,
        rows=rows,
        limitations=[
            "Local synthetic smoke checks; not fault-classification accuracy or a statistically powered latency benchmark.",
            "Model errors measure self-consistency against synthetic reference temperatures; no plant calibration.",
            "Historical matching is covered separately with captured past records.",
        ],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    results = evaluate(args.repeats)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"Completed {results['analysis_count']} synthetic profile checks; output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
