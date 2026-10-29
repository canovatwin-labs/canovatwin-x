"""Window statistics use elapsed seconds, not assumed sampling intervals."""

from itertools import pairwise
from math import sqrt
from statistics import fmean, pvariance

from ..contracts import SignalResult
from ..state import AnalysisContext
from .shared import evidence_for


def signal_metrics(ctx: AnalysisContext) -> dict[str, tuple[float, str]]:
    if ctx.quality is None or not ctx.quality.usable:
        raise ValueError("Signal analysis requires valid telemetry")
    samples = ctx.request.window.samples
    n = max(1, len(samples) // 3)

    def values(field: str) -> list[float]:
        result = [getattr(s, field) for s in samples]
        if any(value is None for value in result):
            raise ValueError("Missing observations cannot be imputed")
        return result

    inlet = values("inlet_c")
    load = values("it_load_kw")
    command = values("fan_command_pct")
    feedback = values("fan_feedback_pct")
    flow = values("airflow_m3s")
    cooling = values("cooling_kw")
    reference = values("reference_inlet_c")
    humidity = values("humidity_pct")
    times = [(s.timestamp - samples[0].timestamp).total_seconds() for s in samples]
    mean_t, mean_temp = fmean(times), fmean(inlet)
    variance_t = sum((t - mean_t) ** 2 for t in times)
    slope = sum((t - mean_t) * (v - mean_temp) for t, v in zip(times, inlet, strict=True)) / variance_t
    expected_flow = fmean(feedback[-n:]) / 100 * ctx.policy.nominal_airflow_m3s
    expected_cooling = fmean(flow[-n:]) / ctx.policy.nominal_airflow_m3s * ctx.policy.nominal_cooling_kw
    # Ratios use 1.0 when demand is effectively zero; no artificial divide-by-zero alarm.
    flow_ratio = fmean(flow[-n:]) / expected_flow if expected_flow > 0.01 else 1.0
    cooling_ratio = fmean(cooling[-n:]) / expected_cooling if expected_cooling > 0.01 else 1.0
    tail = command[-n:]
    changes = [b - a for a, b in pairwise(tail)]
    reversals = sum(a * b < 0 for a, b in pairwise(changes))
    metrics = {
        "inlet_variance_c2": (pvariance(inlet), "degC^2"),
        "inlet_max_c": (max(inlet), "degC"),
        "inlet_rise_c": (fmean(inlet[-n:]) - fmean(inlet[:n]), "degC"),
        "inlet_slope_c_per_min": (slope * 60, "degC/min"),
        "fan_error_pct": (fmean(abs(a - b) for a, b in zip(command[-n:], feedback[-n:], strict=True)), "pct"),
        "airflow_efficiency": (flow_ratio, "ratio"),
        "cooling_efficiency": (cooling_ratio, "ratio"),
        "load_increase_kw": (fmean(load[-n:]) - fmean(load[:n]), "kW"),
        "sensor_disagreement_c": (
            fmean(abs(a - b) for a, b in zip(inlet[-n:], reference[-n:], strict=True)),
            "degC",
        ),
        "fan_variation_pct": (max(command[-n:]) - min(command[-n:]), "pct"),
        "fan_direction_reversals": (float(reversals), "count"),
        "humidity_min_pct": (min(humidity), "pct"),
        "humidity_max_pct": (max(humidity), "pct"),
    }
    centered_temperature = [v - mean_temp for v in inlet]
    mean_feedback = fmean(feedback)
    centered_feedback = [v - mean_feedback for v in feedback]
    denominator = sqrt(sum(v * v for v in centered_temperature) * sum(v * v for v in centered_feedback))
    if denominator > 1e-12:
        correlation = (
            sum(a * b for a, b in zip(centered_temperature, centered_feedback, strict=True)) / denominator
        )
        metrics["fan_temperature_correlation"] = (max(-1.0, min(1.0, correlation)), "ratio")
    # With a constant signal Pearson correlation is undefined, so it is omitted.
    return metrics


def analyze_signals(ctx: AnalysisContext) -> SignalResult:
    return SignalResult(evidence=evidence_for(ctx, "A03", signal_metrics(ctx)))
