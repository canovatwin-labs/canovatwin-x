from datetime import UTC, datetime
from itertools import pairwise

import pytest
from pydantic import ValidationError

from canovatwin.operating import GenerationMetadata, OperatingConditions
from canovatwin.stream_experiment import StreamExperiment, StreamRecipe, run_stream_experiment
from canovatwin.telemetry import Scenario


def recipe(delivery="ordered", scenario=Scenario.NORMAL):
    return StreamRecipe(
        generation=GenerationMetadata(
            scenario=scenario,
            count=120,
            seed=42,
            start=datetime(2026, 10, 31, tzinfo=UTC),
            conditions=OperatingConditions(),
        ),
        delivery=delivery,
    )


def test_ordered_transport_preserves_every_measurement_and_reproduces_hash():
    report = run_stream_experiment(recipe())
    assert report.accepted == report.generated == 120
    assert report.rejected == report.dropped == 0
    assert report.final_state.pending == 0
    assert report.final_state.freshness == "fresh"
    assert report.trace_sha256 == run_stream_experiment(recipe()).trace_sha256
    assert len(report.window.samples) == report.accepted


def test_jitter_rejects_duplicate_and_late_packets_and_only_analyzes_sorted_samples():
    report = run_stream_experiment(recipe("jitter"))
    reasons = {e.reason for e in report.events if e.outcome == "rejected"}
    assert "late" in reasons
    assert "duplicate_id" in reasons
    assert report.accepted + report.rejected == report.generated + 8
    timestamps = [sample.timestamp for sample in report.window.samples]
    assert timestamps == sorted(set(timestamps))
    assert report.final_state.pending == 0


def test_outage_keeps_loss_visible_and_recovers_without_filling_the_gap():
    report = run_stream_experiment(recipe("outage"))
    assert report.dropped == 20
    assert report.accepted == 100
    assert report.generated == report.accepted + report.dropped
    disconnect = next(e for e in report.events if e.outcome == "disconnect")
    assert disconnect.state.connection == "disconnected"
    assert disconnect.state.freshness == "stale"
    assert report.final_state.connection == "connected"
    assert report.final_state.freshness == "fresh"
    stamps = [sample.timestamp for sample in report.window.samples]
    assert max((right - left).total_seconds() for left, right in pairwise(stamps)) == 21


@pytest.mark.parametrize("delivery", ["ordered", "jitter", "outage"])
@pytest.mark.parametrize("scenario", list(Scenario))
def test_all_physical_scenarios_survive_each_transport_without_label_input(delivery, scenario):
    report = run_stream_experiment(recipe(delivery, scenario))
    assert report.accepted >= 3
    assert report.window.source == "synthetic"
    assert "fault_labels" not in report.window.model_dump()
    if scenario == Scenario.COMMUNICATION_LOSS:
        assert report.final_state.freshness == "stale"
    assert run_stream_experiment(report.recipe) == report


def test_saved_trace_rejects_counter_and_fingerprint_corruption():
    report = run_stream_experiment(recipe("jitter"))
    import json

    raw = json.loads(report.model_dump_json())
    raw["rejected"] += 1
    with pytest.raises(ValidationError, match="counters"):
        StreamExperiment.model_validate_json(json.dumps(raw))
    raw["rejected"] -= 1
    raw["trace_sha256"] = "0" * 64
    with pytest.raises(ValidationError, match="fingerprint"):
        StreamExperiment.model_validate_json(json.dumps(raw))


@pytest.mark.parametrize("count", [30, 600])
@pytest.mark.parametrize("delivery", ["ordered", "jitter", "outage"])
def test_boundary_sample_counts_preserve_bounded_sorted_window(count, delivery):
    original = recipe(delivery, Scenario.COMMUNICATION_LOSS)
    spec = original.model_copy(update={"generation": original.generation.model_copy(update={"count": count})})
    report = run_stream_experiment(spec)
    assert 3 <= report.accepted <= 600
    assert report.final_state.pending == 0
