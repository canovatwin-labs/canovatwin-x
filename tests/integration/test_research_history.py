import sqlite3
from contextlib import closing
from datetime import timedelta
from hashlib import sha256
from pathlib import Path

import pytest

from canovatwin.contracts import HistoricalCase, ResearchInputs
from canovatwin.history import HistoryService
from canovatwin.knowledge import demo_documents
from canovatwin.persistence.errors import ReplayIncompatible
from canovatwin.persistence.models import RecordedAnalysis
from canovatwin.persistence.sqlite import SQLiteRepository
from canovatwin.snapshots import capture_history
from canovatwin.telemetry import Scenario


def earlier(request, days=1):
    samples = tuple(
        s.model_copy(update={"timestamp": s.timestamp - timedelta(days=days)}) for s in request.window.samples
    )
    return request.model_copy(
        update={
            "window": request.window.model_copy(update={"samples": samples}),
            "as_of": request.as_of - timedelta(days=days),
        }
    )


def test_history_snapshot_replay_is_not_changed_by_new_records(tmp_path, request_factory):
    with SQLiteRepository(tmp_path / "history.sqlite3", create=True) as repo:
        service = HistoryService(repo)
        request = request_factory(Scenario.FAN_LOSS)
        old = service.analyze(earlier(request))
        extended = request.model_copy(update={"research": ResearchInputs(documents=demo_documents())})
        captured = capture_history(repo, extended)
        assert [c.run_id for c in captured.research.historical_cases] == [old.run_id]
        original = service.analyze(captured)
        assert len(original.result.trace) == 11
        assert original.result.report.research.historical_matches[0].run_id == old.run_id
        newer = service.analyze(earlier(request, days=2))
        fresh = capture_history(repo, extended)
        assert {c.run_id for c in fresh.research.historical_cases} == {old.run_id, newer.run_id}
        replay = service.replay(original.run_id)
        assert replay.matches
        assert replay.record.request == original.request
        assert len(replay.record.request.research.historical_cases) == 1


def test_capture_skips_normal_other_asset_and_overlapping_windows(tmp_path, request_factory):
    with SQLiteRepository(tmp_path / "history.sqlite3", create=True) as repo:
        service = HistoryService(repo)
        request = request_factory(Scenario.FAN_LOSS)
        service.analyze(earlier(request_factory()))
        other = earlier(request).model_copy(
            update={"window": earlier(request).window.model_copy(update={"asset_id": "other"})}
        )
        service.analyze(other)
        service.analyze(request)
        extended = request.model_copy(update={"research": ResearchInputs()})
        assert capture_history(repo, extended).research.historical_cases == ()
        assert capture_history(repo, request) == request


def test_explicit_snapshot_is_preserved(tmp_path, request_factory):
    request = request_factory(Scenario.FAN_LOSS)
    case = HistoricalCase(
        run_id="RUN-explicit",
        incident_id="INC-explicit",
        asset_id=request.window.asset_id,
        window_start=request.window.samples[0].timestamp - timedelta(days=2),
        window_end=request.window.samples[-1].timestamp - timedelta(days=2),
        engine_version="0.3.0",
        observation_codes=("FAN_TRACKING",),
        candidate_faults=(),
    )
    request = request.model_copy(update={"research": ResearchInputs(historical_cases=(case,))})
    with SQLiteRepository(tmp_path / "history.sqlite3", create=True) as repo:
        assert capture_history(repo, request) == request


def test_v03_archive_can_be_read_without_rewriting_it(tmp_path):
    raw = (Path(__file__).resolve().parents[1] / "fixtures/legacy_v03_record.json").read_text()
    record = RecordedAnalysis.model_validate_json(raw)
    assert record.request.research is None and record.engine_version == "0.3.0"
    path = tmp_path / "legacy.sqlite3"
    with SQLiteRepository(path, create=True) as repo:
        repo.save(record)
    # Put the actual 0.3.0 serialized form into the database: no new optional fields.
    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            "UPDATE analysis_runs SET payload=?, checksum=?", (raw, sha256(raw.encode()).hexdigest())
        )
        connection.commit()
    with SQLiteRepository(path) as repo:
        loaded = repo.get_run(record.run_id)
        assert loaded == record
        assert repo.save(loaded) == loaded
        with pytest.raises(ReplayIncompatible):
            HistoryService(repo).replay(record.run_id)
    with closing(sqlite3.connect(path)) as connection:
        assert connection.execute("SELECT payload FROM analysis_runs").fetchone()[0] == raw


def test_other_assets_do_not_starve_an_assets_historical_case_limit(tmp_path, request_factory):
    with SQLiteRepository(tmp_path / "assets.sqlite3", create=True) as repo:
        service = HistoryService(repo)
        request = request_factory(Scenario.FAN_LOSS)
        old = service.analyze(earlier(request))
        for index in range(101):
            other = earlier(request).model_copy(
                update={"window": earlier(request).window.model_copy(update={"asset_id": f"other-{index}"})}
            )
            service.analyze(other)
        extended = request.model_copy(update={"research": ResearchInputs(documents=demo_documents())})
        captured = capture_history(repo, extended)
        assert [case.run_id for case in captured.research.historical_cases] == [old.run_id]
