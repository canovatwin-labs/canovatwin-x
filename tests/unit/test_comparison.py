from datetime import UTC, datetime, timedelta

import pytest

from canovatwin.comparison import ComparisonConflict, compare_runs
from canovatwin.contracts import AnalysisRequest
from canovatwin.history import HistoryService
from canovatwin.persistence.sqlite import SQLiteRepository
from canovatwin.policy import Policy
from canovatwin.telemetry import Scenario, generate_case


@pytest.fixture
def records(tmp_path):
    case = generate_case(Scenario.NORMAL, start=datetime(2026, 10, 31, tzinfo=UTC), count=30)
    with SQLiteRepository(tmp_path / "history.sqlite3", create=True) as repository:
        service = HistoryService(repository)
        before = service.analyze(AnalysisRequest(window=case.window, as_of=case.observation_time))
        samples = tuple(
            sample.model_copy(update={"inlet_c": 30.0, "humidity_pct": None})
            for sample in case.window.samples
        )
        # Last measured inlet is explicitly missing; do not substitute an earlier reading.
        samples = (*samples[:-1], samples[-1].model_copy(update={"inlet_c": None}))
        after = service.analyze(
            AnalysisRequest(
                window=case.window.model_copy(update={"samples": samples}), as_of=case.observation_time
            )
        )
        return before, after


def test_direction_missing_counts_and_final_value_are_explicit(records):
    before, after = records
    result = compare_runs(before, after)
    inlet = next(channel for channel in result.channels if channel.field == "inlet_c")
    assert inlet.candidate.valid_count == 29 and inlet.candidate.missing_count == 1
    assert inlet.candidate.mean == 30
    assert inlet.mean_delta == pytest.approx(30 - inlet.baseline.mean)
    assert inlet.candidate.final is None and inlet.final_delta is None
    humidity = next(channel for channel in result.channels if channel.field == "humidity_pct")
    assert humidity.candidate.valid_count == 0 and humidity.candidate.missing_count == 30
    assert humidity.candidate.mean is humidity.candidate.minimum is humidity.candidate.maximum is None
    assert humidity.mean_delta is humidity.final_delta is None
    reverse = compare_runs(after, before)
    assert next(c for c in reverse.channels if c.field == "inlet_c").mean_delta == -inlet.mean_delta
    assert result.same_measurement_timestamps is True


def test_differences_expose_engine_and_policy_changes(records):
    before, after = records
    modified = after.model_copy(
        update={
            "engine_version": "future-engine",
            "policy": after.policy.model_copy(update={"max_tool_calls": 1}),
        }
    )
    result = compare_runs(before, modified)
    assert "engine_version" in result.differing_inputs
    assert "policy.max_tool_calls" in result.differing_inputs


def test_extreme_delta_is_rejected_instead_of_serializing_infinity(records):
    before, after = records

    def replace(record, value):
        samples = tuple(s.model_copy(update={"inlet_c": value}) for s in record.request.window.samples)
        return record.model_copy(
            update={
                "request": record.request.model_copy(
                    update={"window": record.request.window.model_copy(update={"samples": samples})}
                )
            }
        )

    with pytest.raises(ComparisonConflict, match="numeric range"):
        compare_runs(replace(before, -1e308), replace(after, 1e308))


def test_final_reading_uses_timestamp_not_array_position(records):
    before, after = records
    reversed_window = after.request.window.model_copy(
        update={"samples": tuple(reversed(after.request.window.samples))}
    )
    reordered = after.model_copy(
        update={"request": after.request.model_copy(update={"window": reversed_window})}
    )
    result = compare_runs(before, reordered)
    assert next(c for c in result.channels if c.field == "inlet_c").candidate.final is None
    assert result.same_measurement_timestamps is False


def test_time_shift_is_visible_even_when_values_match(records):
    before, after = records
    shifted = tuple(
        sample.model_copy(update={"timestamp": sample.timestamp + timedelta(hours=1)})
        for sample in after.request.window.samples
    )
    after = after.model_copy(
        update={
            "request": after.request.model_copy(
                update={"window": after.request.window.model_copy(update={"samples": shifted})}
            )
        }
    )
    result = compare_runs(before, after)
    assert result.same_measurement_timestamps is False
    assert result.candidate.window_start - result.baseline.window_start == timedelta(hours=1)


def test_blocked_analysis_can_be_compared_without_inventing_a_report(records, tmp_path):
    before, changed = records
    with SQLiteRepository(tmp_path / "blocked.sqlite3", create=True) as repository:
        after = HistoryService(repository).analyze(changed.request, policy=Policy(max_agents=1))
    assert after.result.status == "blocked"
    result = compare_runs(before, after)
    assert result.candidate.analysis_status == "blocked"
    assert result.candidate.report_status is None
    assert result.candidate.transport_dropped is None
    assert result.candidate.kind == "reference_or_custom"
    assert "telemetry_sha256" in result.differing_inputs


def test_large_finite_values_have_a_finite_mean(records):
    before, after = records
    samples = tuple(sample.model_copy(update={"inlet_c": 1e308}) for sample in after.request.window.samples)
    after = after.model_copy(
        update={
            "request": after.request.model_copy(
                update={"window": after.request.window.model_copy(update={"samples": samples})}
            )
        }
    )
    result = compare_runs(before, after)
    inlet = next(channel for channel in result.channels if channel.field == "inlet_c")
    assert inlet.candidate.mean == 1e308
    assert inlet.mean_delta == 1e308
