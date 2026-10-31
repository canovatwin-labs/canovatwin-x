"""Read-only descriptive comparison of two immutable runs, never a causal ranking."""

from hashlib import sha256
from math import isfinite
from statistics import mean
from typing import Literal

from pydantic import AwareDatetime, Field

from .assets import CHANNELS
from .contracts import Contract, Identifier
from .persistence.models import RecordedAnalysis


class ComparisonConflict(ValueError):
    """The selected records cannot form a safe, same-asset comparison."""


class ChannelStatistics(Contract):
    valid_count: int = Field(ge=0, le=600)
    missing_count: int = Field(ge=0, le=600)
    minimum: float | None
    maximum: float | None
    mean: float | None
    # The final timestamp's actual reading, not a forward-filled earlier value.
    final: float | None


class ChannelComparison(Contract):
    field: str
    name: str
    unit: str
    baseline: ChannelStatistics
    candidate: ChannelStatistics
    mean_delta: float | None
    final_delta: float | None


class ComparedRun(Contract):
    run_id: Identifier
    incident_id: Identifier
    recorded_at: AwareDatetime
    engine_version: str
    source: Literal["synthetic", "declared_external"]
    kind: Literal["reference_or_custom", "dynamic", "stream"]
    sample_count: int
    window_start: AwareDatetime
    window_end: AwareDatetime
    analysis_status: Literal["completed", "blocked"]
    report_status: Literal["clear", "needs_review", "insufficient_data"] | None
    transport_accepted: int | None
    transport_rejected: int | None
    transport_dropped: int | None


class RunComparison(Contract):
    comparison_version: Literal["comparison-1.0"] = "comparison-1.0"
    asset_id: Identifier
    baseline: ComparedRun
    candidate: ComparedRun
    channels: tuple[ChannelComparison, ...]
    differing_inputs: tuple[str, ...]
    same_measurement_timestamps: bool
    limitations: tuple[str, ...] = (
        "Descriptive comparison only; deltas are candidate minus baseline, not a causal improvement score.",
        "Means use available readings without imputation or time weighting; missingness can change them.",
        "Unequal windows and changed inputs may confound comparison; no pointwise alignment is performed.",
        "Cooling power is thermal power; electrical consumption, energy savings and PUE are not inferred.",
        "Candidate fault labels and report statuses are unconfirmed, not diagnostic ground truth.",
    )


def _kind(record: RecordedAnalysis) -> str:
    return "stream" if record.stream_experiment else "dynamic" if record.generation else "reference_or_custom"


def _summary(record: RecordedAnalysis) -> ComparedRun:
    samples = record.request.window.samples
    transport = record.stream_experiment
    return ComparedRun(
        run_id=record.run_id,
        incident_id=record.result.incident_id,
        recorded_at=record.recorded_at,
        engine_version=record.engine_version,
        source=record.request.window.source,
        kind=_kind(record),
        sample_count=len(samples),
        window_start=min(sample.timestamp for sample in samples),
        window_end=max(sample.timestamp for sample in samples),
        analysis_status=record.result.status,
        report_status=record.result.report.status if record.result.report else None,
        transport_accepted=transport.accepted if transport else None,
        transport_rejected=transport.rejected if transport else None,
        transport_dropped=transport.dropped if transport else None,
    )


def _context(record: RecordedAnalysis) -> dict:
    transport = record.stream_experiment
    generation = transport.recipe.generation if transport else record.generation
    request = record.request
    return {
        "engine_version": record.engine_version,
        "source": request.window.source,
        "clock_mode": request.clock_mode,
        "as_of": request.as_of.isoformat(),
        "kind": _kind(record),
        "policy": record.policy.model_dump(mode="json"),
        "research": request.research.model_dump(mode="json") if request.research else None,
        "generation": generation.model_dump(mode="json") if generation else None,
        "transport": transport.recipe.delivery if transport else None,
        "sample_count": len(request.window.samples),
        "telemetry_sha256": sha256(request.window.model_dump_json().encode()).hexdigest(),
    }


def _differences(left, right, prefix="") -> tuple[str, ...]:
    if isinstance(left, dict) and isinstance(right, dict):
        return tuple(
            path
            for key in sorted(left.keys() | right.keys())
            for path in _differences(left.get(key), right.get(key), f"{prefix}.{key}" if prefix else key)
        )
    return (prefix,) if left != right else ()


def _statistics(record: RecordedAnalysis, field: str) -> ChannelStatistics:
    samples = record.request.window.samples
    values = [getattr(sample, field) for sample in samples if getattr(sample, field) is not None]
    # statistics.mean uses exact accumulation and handles large finite values.
    return ChannelStatistics(
        valid_count=len(values),
        missing_count=len(samples) - len(values),
        minimum=min(values) if values else None,
        maximum=max(values) if values else None,
        mean=mean(values) if values else None,
        final=getattr(max(samples, key=lambda sample: sample.timestamp), field),
    )


def _delta(before: float | None, after: float | None) -> float | None:
    if before is None or after is None:
        return None
    value = after - before
    if not isfinite(value):
        raise ComparisonConflict("Channel difference exceeds the supported numeric range")
    return value


def compare_runs(baseline: RecordedAnalysis, candidate: RecordedAnalysis) -> RunComparison:
    if baseline.run_id == candidate.run_id:
        raise ComparisonConflict("Choose two distinct recorded runs")
    if baseline.request.window.asset_id != candidate.request.window.asset_id:
        raise ComparisonConflict("Both runs must belong to the same asset")
    channels = []
    for channel in CHANNELS:
        before, after = _statistics(baseline, channel.field), _statistics(candidate, channel.field)
        channels.append(
            ChannelComparison(
                field=channel.field,
                name=channel.name,
                unit=channel.unit,
                baseline=before,
                candidate=after,
                mean_delta=_delta(before.mean, after.mean),
                final_delta=_delta(before.final, after.final),
            )
        )

    def timestamps(record):
        return tuple(sample.timestamp for sample in record.request.window.samples)

    return RunComparison(
        asset_id=baseline.request.window.asset_id,
        baseline=_summary(baseline),
        candidate=_summary(candidate),
        channels=tuple(channels),
        differing_inputs=_differences(_context(baseline), _context(candidate)),
        same_measurement_timestamps=timestamps(baseline) == timestamps(candidate),
    )
