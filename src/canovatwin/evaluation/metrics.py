"""Explicit denominators; failed runs remain visible outside conditional scores."""

from statistics import mean

from ..contracts import FaultCode
from .models import CaseResult, ClassificationScore, Method, MethodSummary


def ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def score(tp: int, fp: int, fn: int) -> ClassificationScore:
    return ClassificationScore(
        tp=tp,
        fp=fp,
        fn=fn,
        precision=ratio(tp, tp + fp),
        recall=ratio(tp, tp + fn),
        f1=ratio(2 * tp, 2 * tp + fp + fn),
    )


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def summarize(method: Method, rows: tuple[CaseResult, ...]) -> MethodSummary:
    rows = tuple(row for row in rows if row.method == method)
    if not rows:
        raise ValueError("Cannot score an empty method")
    valid = [row for row in rows if row.prediction.status != "blocked"]
    truth = [bool(row.truth) for row in valid]
    alarms = [row.prediction.status != "clear" for row in valid]
    tp = sum(a and b for a, b in zip(truth, alarms, strict=True))
    fp = sum(not a and b for a, b in zip(truth, alarms, strict=True))
    fn = sum(a and not b for a, b in zip(truth, alarms, strict=True))
    tn = sum(not a and not b for a, b in zip(truth, alarms, strict=True))
    labels = {}
    for label in FaultCode:
        if label == FaultCode.COMBINED:
            continue
        actual = [label in row.truth for row in valid]
        predicted = [label in row.prediction.predicted for row in valid]
        labels[label] = score(
            sum(a and b for a, b in zip(actual, predicted, strict=True)),
            sum(not a and b for a, b in zip(actual, predicted, strict=True)),
            sum(a and not b for a, b in zip(actual, predicted, strict=True)),
        )
    f1s = [item.f1 for item in labels.values() if item.f1 is not None]
    top3 = [
        len(set(row.truth) & set(row.prediction.predicted[:3])) / len(row.truth) for row in valid if row.truth
    ]
    verified = [
        row.prediction.verification_passed for row in rows if row.prediction.verification_passed is not None
    ]
    model = [
        row.prediction
        for row in valid
        if row.prediction.model_mae_c is not None and row.prediction.model_rmse_c is not None
    ]
    return MethodSummary(
        method=method,
        total=len(rows),
        scored=len(valid),
        blocked=len(rows) - len(valid),
        coverage=len(valid) / len(rows),
        insufficient_data=sum(row.prediction.status == "insufficient_data" for row in valid),
        alarm=score(tp, fp, fn),
        true_negatives=tn,
        false_alarm_rate=ratio(fp, fp + tn),
        labels=labels,
        macro_f1=mean(f1s) if f1s else None,
        top3_fault_recall=mean(top3) if top3 else None,
        latency_p50_ms=percentile([row.elapsed_ms for row in rows], 0.5),
        latency_p95_ms=percentile([row.elapsed_ms for row in rows], 0.95),
        mean_active_agents=mean(row.prediction.active_agents for row in rows),
        verification_pass_rate=mean(verified) if verified else None,
        model_cases=len(model),
        mean_model_mae_c=mean(item.model_mae_c for item in model) if model else None,
        mean_model_rmse_c=mean(item.model_rmse_c for item in model) if model else None,
    )
