from datetime import UTC, datetime

import pytest

from canovatwin.history import HistoryService, compare_results
from canovatwin.persistence.errors import Conflict, NotFound, ReplayIncompatible
from canovatwin.persistence.models import IncidentStatus, Transition
from canovatwin.persistence.sqlite import SQLiteRepository
from canovatwin.policy import Policy
from canovatwin.telemetry import Scenario


@pytest.fixture
def repo(tmp_path):
    with SQLiteRepository(tmp_path / "history.sqlite3", create=True) as repository:
        yield repository


def test_replay_reuses_input_policy_and_preserves_original(repo, request_factory):
    service = HistoryService(repo)
    original = service.analyze(request_factory(Scenario.LOAD_SURGE), policy=Policy(load_increase_kw=2.0))
    replay = service.replay(original.run_id)
    assert replay.matches and replay.differences == ()
    assert replay.record.run_id != original.run_id
    assert replay.record.replay_of == original.run_id
    assert replay.record.request == original.request and replay.record.policy == original.policy
    assert replay.record.result.report == original.result.report
    assert repo.get_run(original.run_id) == original
    assert repo.get_run(replay.record.run_id) == replay.record
    assert repo.get_incident(original.result.incident_id).run_count == 2


def test_replay_does_not_reopen_closed_incident(repo, request_factory):
    service = HistoryService(repo)
    original = service.analyze(request_factory())
    incident_id = original.result.incident_id
    repo.transition(
        Transition(
            incident_id=incident_id,
            target=IncidentStatus.INVESTIGATING,
            expected_revision=1,
            actor="engineer",
            reason="Review",
        )
    )
    repo.transition(
        Transition(
            incident_id=incident_id,
            target=IncidentStatus.CLOSED,
            expected_revision=2,
            actor="engineer",
            reason="Review complete",
        )
    )
    service.replay(original.run_id)
    incident = repo.get_incident(incident_id)
    assert incident.status == IncidentStatus.CLOSED
    assert incident.revision == 4 and incident.run_count == 2


def test_replay_version_mismatch_fails_before_saving(repo, request_factory):
    original = HistoryService(repo).analyze(request_factory())
    old = original.model_copy(update={"run_id": "RUN-older-engine", "engine_version": "0.2.0"})
    repo.save(old)
    with pytest.raises(ReplayIncompatible):
        HistoryService(repo).replay(old.run_id)
    assert repo.get_incident(original.result.incident_id).run_count == 2


def test_missing_replay_and_mismatched_inputs_cannot_create_orphan_records(repo, request_factory):
    service = HistoryService(repo)
    with pytest.raises(NotFound):
        service.replay("RUN-missing")
    assert repo.list_incidents() == ()
    original = service.analyze(request_factory())
    with pytest.raises(Conflict):
        service.analyze(request_factory(Scenario.FAN_LOSS), replay_of=original.run_id)
    assert len(repo.list_incidents()) == 1
    assert repo.get_incident(original.result.incident_id).run_count == 1


def test_new_analysis_invalidates_previous_revision(repo, request_factory):
    service = HistoryService(repo)
    original = service.analyze(request_factory())
    service.analyze(request_factory())
    with pytest.raises(Conflict):
        repo.transition(
            Transition(
                incident_id=original.result.incident_id,
                target=IncidentStatus.INVESTIGATING,
                expected_revision=1,
                actor="engineer",
                reason="Based on old result",
            )
        )


def test_compare_ignores_only_elapsed_time(repo, request_factory):
    run = HistoryService(repo).analyze(request_factory()).result
    trace = (run.trace[0].model_copy(update={"elapsed_ms": 999.0}),) + run.trace[1:]
    assert compare_results(run, run.model_copy(update={"trace": trace})) == ()
    trace = (trace[0].model_copy(update={"tool_calls": 99}),) + trace[1:]
    assert compare_results(run, run.model_copy(update={"trace": trace})) == ("trace",)
    altered = run.model_copy(update={"report": run.report.model_copy(update={"summary": "Different"})})
    assert compare_results(run, altered) == ("report",)


def test_replay_exposes_changed_results(repo, request_factory, monkeypatch):
    import canovatwin.history as history

    service = HistoryService(repo)
    original = service.analyze(request_factory())
    real_run = history.Supervisor.run

    def changed(self, request):
        result = real_run(self, request)
        report = result.report.model_copy(update={"summary": "Changed output"})
        outputs = result.outputs[:-1] + (result.outputs[-1].model_copy(update={"payload": report}),)
        return result.model_copy(update={"report": report, "outputs": outputs})

    monkeypatch.setattr(history.Supervisor, "run", changed)
    replay = service.replay(original.run_id)
    assert not replay.matches and "report" in replay.differences
    assert repo.get_run(original.run_id) == original


def test_blocked_analysis_replays_as_blocked_without_report(repo, request_factory):
    service = HistoryService(repo)
    original = service.analyze(request_factory(), policy=Policy(max_agents=1))
    replay = service.replay(original.run_id)
    assert replay.matches
    assert replay.record.result.status == "blocked"
    assert replay.record.result.report is None


def test_older_recording_time_does_not_move_updated_time_back(repo, request_factory):
    first = HistoryService(repo, clock=lambda: datetime(2026, 10, 28, tzinfo=UTC)).analyze(request_factory())
    HistoryService(repo, clock=lambda: datetime(2026, 10, 27, tzinfo=UTC)).analyze(request_factory())
    summary = repo.get_incident(first.result.incident_id)
    assert summary.updated_at == first.recorded_at and summary.revision == 2
