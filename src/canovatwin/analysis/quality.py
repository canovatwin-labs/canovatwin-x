"""Data quality remains reportable even when physical diagnosis is impossible."""

from itertools import pairwise

from ..contracts import Observation, QualityResult
from ..state import AnalysisContext
from .shared import evidence_for

# Illustrative sensor operating bounds; not manufacturer limits.
BOUNDS = {
    "inlet_c": (-20, 80),
    "reference_inlet_c": (-20, 80),
    "return_c": (-20, 100),
    "supply_c": (-20, 80),
    "ambient_c": (-40, 80),
    "humidity_pct": (0, 100),
    "fan_command_pct": (0, 100),
    "fan_feedback_pct": (0, 100),
    "airflow_m3s": (0, 20),
    "it_load_kw": (0, 1000),
    "cooling_kw": (0, 1000),
}


def quality_metrics(ctx: AnalysisContext) -> dict[str, tuple[float, str]]:
    samples = ctx.request.window.samples
    timestamps = [s.timestamp for s in samples]
    gaps = [(b - a).total_seconds() for a, b in pairwise(timestamps)]
    missing = sum(getattr(s, field) is None for s in samples for field in BOUNDS)
    invalid = sum(
        value is not None and not low <= value <= high
        for s in samples
        for field, (low, high) in BOUNDS.items()
        for value in (getattr(s, field),)
    )
    return {
        "missing_values": (float(missing), "count"),
        "out_of_range_values": (float(invalid), "count"),
        "air_temperature_order_violations": (
            float(
                sum(
                    s.supply_c is not None and s.return_c is not None and s.return_c < s.supply_c - 0.5
                    for s in samples
                )
            ),
            "count",
        ),
        "duplicate_sample_ids": (float(len(samples) - len({s.sample_id for s in samples})), "count"),
        "non_increasing_timestamps": (float(sum(gap <= 0 for gap in gaps)), "count"),
        "max_gap_s": (max(gaps), "s"),
        "window_span_s": ((max(timestamps) - min(timestamps)).total_seconds(), "s"),
        "latest_age_s": ((ctx.request.as_of - max(timestamps)).total_seconds(), "s"),
    }


def check_quality(ctx: AnalysisContext) -> QualityResult:
    metrics = quality_metrics(ctx)
    evidence = evidence_for(ctx, "A02", metrics)
    by_metric = {e.metric: e.evidence_id for e in evidence}
    p = ctx.policy
    checks = (
        ("missing_values", metrics["missing_values"][0] > 0, "Eksik sensör ölçümü var."),
        (
            "out_of_range_values",
            metrics["out_of_range_values"][0] > 0,
            "Ölçüm fiziksel kontrol aralığı dışında.",
        ),
        (
            "air_temperature_order_violations",
            metrics["air_temperature_order_violations"][0] > 0,
            "Dönüş havası üfleme havasından daha soğuk; soğutma modu ve sensör eşlemesi incelenmeli.",
        ),
        ("duplicate_sample_ids", metrics["duplicate_sample_ids"][0] > 0, "Tekrarlanan ölçüm kimliği var."),
        ("non_increasing_timestamps", metrics["non_increasing_timestamps"][0] > 0, "Zaman sırası geçersiz."),
        ("max_gap_s", metrics["max_gap_s"][0] > p.max_gap_s, "Ölçümler arasında veri boşluğu var."),
        ("window_span_s", metrics["window_span_s"][0] > p.max_window_s, "İnceleme penceresi fazla uzun."),
        ("latest_age_s", metrics["latest_age_s"][0] > p.max_age_s, "Son telemetri güncel değil."),
        (
            "latest_age_s",
            metrics["latest_age_s"][0] < -p.future_tolerance_s,
            "Telemetri gelecekte görünüyor.",
        ),
    )
    issues = tuple(
        Observation(code=f"QUALITY_{metric.upper()}", message=message, evidence_ids=(by_metric[metric],))
        for metric, failed, message in checks
        if failed
    )
    return QualityResult(usable=not issues, issues=issues, evidence=evidence)
