import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from hashlib import sha256

import pytest
from pydantic import ValidationError

from canovatwin.history import HistoryService
from canovatwin.persistence.errors import (
    Conflict,
    CorruptRecord,
    InvalidTransition,
    NotFound,
    StorageBusy,
    StorageError,
    UnsupportedSchema,
)
from canovatwin.persistence.models import IncidentStatus, RecordedAnalysis, Transition
from canovatwin.persistence.sqlite import SQLiteRepository
from canovatwin.telemetry import Scenario


def execute(path, sql, parameters=()):
    with closing(sqlite3.connect(path)) as db:
        result = db.execute(sql, parameters).fetchall()
        db.commit()
        return result


@pytest.fixture
def path(tmp_path):
    return tmp_path / "history.sqlite3"


@pytest.fixture
def record(path, request_factory):
    with SQLiteRepository(path, create=True) as repo:
        return HistoryService(repo).analyze(request_factory(Scenario.FAN_LOSS))


def test_roundtrip_after_closing_database(path, record):
    with SQLiteRepository(path, read_only=True) as repo:
        assert repo.get_run(record.run_id) == record
        incident = repo.get_incident(record.result.incident_id)
        assert incident.run_count == 1 and incident.revision == 1
        assert incident.latest_run_id == record.run_id
        assert incident.latest_report_status == "needs_review"
        assert incident.status == IncidentStatus.OPEN
        assert len(repo.list_runs(incident.incident_id)) == 1
        assert [e.action for e in reversed(repo.audit(incident.incident_id))] == [
            "incident_created",
            "analysis_saved",
        ]


def test_unique_runs_share_incident_and_keep_evidence_isolated(path, record):
    with SQLiteRepository(path) as repo:
        second = HistoryService(repo).analyze(record.request)
        assert second.run_id != record.run_id
        assert second.result.incident_id == record.result.incident_id
        assert repo.get_run(record.run_id) == record
        assert repo.get_run(second.run_id) == second
        assert repo.get_incident(record.result.incident_id).run_count == 2
        assert repo.get_incident(record.result.incident_id).revision == 2
        assert [s.run_id for s in repo.list_runs(record.result.incident_id)] == [second.run_id, record.run_id]


def test_save_retry_is_idempotent_and_different_payload_conflicts(path, record):
    with SQLiteRepository(path) as repo:
        assert repo.save(record) == record
        assert len(repo.audit(record.result.incident_id)) == 2
        assert repo.get_incident(record.result.incident_id).revision == 1
        with pytest.raises(Conflict):
            repo.save(record.model_copy(update={"actor": "someone-else"}))
        assert repo.get_run(record.run_id) == record


def test_failed_write_rolls_back_entire_incident(path, request_factory):
    with SQLiteRepository(path, create=True):
        pass
    execute(
        path,
        "CREATE TRIGGER fail_audit BEFORE INSERT ON audit_events WHEN NEW.action='analysis_saved' BEGIN SELECT RAISE(ABORT, 'secret-sql'); END",
    )
    with SQLiteRepository(path) as repo:
        with pytest.raises(StorageError) as error:
            HistoryService(repo).analyze(request_factory())
        assert "secret-sql" not in str(error.value)
        assert repo.list_incidents() == ()
    for table in ("incidents", "analysis_runs", "evidence", "agent_runs", "audit_events"):
        assert execute(path, f"SELECT COUNT(*) FROM {table}")[0][0] == 0


def test_failed_second_write_keeps_prior_revision_and_data(path, record):
    execute(
        path, "CREATE TRIGGER fail_detail BEFORE INSERT ON evidence BEGIN SELECT RAISE(ABORT, 'test'); END"
    )
    with SQLiteRepository(path) as repo:
        before = repo.get_incident(record.result.incident_id)
        with pytest.raises(StorageError):
            HistoryService(repo).analyze(record.request)
        assert repo.get_incident(record.result.incident_id) == before
        assert repo.get_run(record.run_id) == record
        assert len(repo.audit(before.incident_id)) == 2


def test_missing_database_read_does_not_create_file(path):
    with pytest.raises(NotFound):
        SQLiteRepository(path)
    assert not path.exists()


def test_readonly_connection_cannot_write(path, record):
    with SQLiteRepository(path, read_only=True) as repo:
        assert repo.get_run(record.run_id) == record
        with pytest.raises(StorageError, match="read-only"):
            repo.save(record)
    assert len(execute(path, "SELECT * FROM analysis_runs")) == 1


def test_unknown_database_is_preserved(path):
    execute(path, "CREATE TABLE personal_data (value TEXT)")
    execute(path, "INSERT INTO personal_data VALUES (?)", ("keep-me",))
    with pytest.raises(UnsupportedSchema):
        SQLiteRepository(path, create=True)
    assert execute(path, "SELECT value FROM personal_data") == [("keep-me",)]
    assert execute(path, "PRAGMA user_version") == [(0,)]


def test_future_schema_version_rejected(path, record):
    execute(path, "PRAGMA user_version=2")
    with pytest.raises(UnsupportedSchema):
        SQLiteRepository(path)
    assert execute(path, "SELECT COUNT(*) FROM analysis_runs") == [(1,)]


def test_incomplete_schema_rejected(path, record):
    execute(path, "DROP TABLE audit_events")
    with pytest.raises(CorruptRecord):
        SQLiteRepository(path)


def test_non_database_file_rejected_without_data_leak(path):
    path.write_text("private-data")
    with pytest.raises(StorageError) as error:
        SQLiteRepository(path)
    assert "private-data" not in str(error.value)
    assert path.read_text() == "private-data"


@pytest.mark.parametrize("tamper", ["payload", "metadata", "evidence", "trace", "shape"])
def test_corrupted_records_never_return_as_valid_history(path, record, tamper):
    if tamper == "payload":
        execute(path, "UPDATE analysis_runs SET payload='{}'")
    elif tamper == "metadata":
        execute(path, "UPDATE analysis_runs SET engine_version='fake'")
    elif tamper == "evidence":
        execute(path, "UPDATE evidence SET payload='{}' WHERE ordinal=0")
    elif tamper == "trace":
        execute(path, "DELETE FROM agent_runs WHERE ordinal=0")
    else:
        execute(path, "UPDATE analysis_runs SET payload=?, checksum=?", ("{}", sha256(b"{}").hexdigest()))
    with SQLiteRepository(path) as repo:
        with pytest.raises(CorruptRecord):
            repo.get_run(record.run_id)


def test_unknown_ids_and_parameterized_queries(path, record):
    with SQLiteRepository(path) as repo:
        for method in (repo.get_run, repo.get_incident, repo.list_runs, repo.audit):
            with pytest.raises(NotFound):
                method("'; DROP TABLE incidents;--")
        assert repo.get_run(record.run_id) == record


@pytest.mark.parametrize(("limit", "offset"), [(0, 0), (101, 0), (1, -1), (True, 0), (1, False)])
def test_invalid_pagination(path, record, limit, offset):
    with SQLiteRepository(path) as repo:
        with pytest.raises(ValueError):
            repo.list_incidents(limit=limit, offset=offset)


def test_pagination_and_filters(path, request_factory):
    with SQLiteRepository(path, create=True) as repo:
        service = HistoryService(repo)
        first = service.analyze(request_factory())
        second = service.analyze(request_factory(Scenario.COOLING_LOSS))
        repo.transition(
            Transition(
                incident_id=first.result.incident_id,
                target=IncidentStatus.INVESTIGATING,
                expected_revision=1,
                actor="engineer",
                reason="Begin review",
            )
        )
        assert repo.list_incidents(limit=1)[0].incident_id == second.result.incident_id
        assert repo.list_incidents(limit=1, offset=1)[0].incident_id == first.result.incident_id
        assert (
            repo.list_incidents(status=IncidentStatus.INVESTIGATING)[0].incident_id
            == first.result.incident_id
        )
        assert repo.list_runs(first.result.incident_id, offset=1) == ()
        assert len(repo.audit(first.result.incident_id, limit=1, offset=1)) == 1
        with pytest.raises(ValueError):
            repo.list_incidents(status="open")


def test_lifecycle_audit_and_reopen(path, record):
    with SQLiteRepository(path) as repo:
        incident_id = record.result.incident_id
        for revision, target in [
            (1, IncidentStatus.INVESTIGATING),
            (2, IncidentStatus.CLOSED),
            (3, IncidentStatus.OPEN),
        ]:
            updated = repo.transition(
                Transition(
                    incident_id=incident_id,
                    target=target,
                    expected_revision=revision,
                    actor="engineer",
                    reason="Test review decision",
                )
            )
            assert updated.status == target and updated.revision == revision + 1
        events = [e for e in reversed(repo.audit(incident_id)) if e.action == "status_changed"]
        assert [(e.old_status, e.new_status) for e in events] == [
            (IncidentStatus.OPEN, IncidentStatus.INVESTIGATING),
            (IncidentStatus.INVESTIGATING, IncidentStatus.CLOSED),
            (IncidentStatus.CLOSED, IncidentStatus.OPEN),
        ]
        assert all(e.actor == "engineer" and e.reason == "Test review decision" for e in events)
        assert repo.get_run(record.run_id) == record


def test_illegal_transition_does_not_write_audit(path, record):
    with SQLiteRepository(path) as repo:
        for target in (IncidentStatus.CLOSED, IncidentStatus.OPEN):
            with pytest.raises(InvalidTransition):
                repo.transition(
                    Transition(
                        incident_id=record.result.incident_id,
                        target=target,
                        expected_revision=1,
                        actor="engineer",
                        reason="Not allowed",
                    )
                )
        assert repo.get_incident(record.result.incident_id).revision == 1
        assert len(repo.audit(record.result.incident_id)) == 2


def test_stale_revision_from_second_connection_is_rejected(path, record):
    with SQLiteRepository(path) as first, SQLiteRepository(path) as second:
        incident = first.get_incident(record.result.incident_id)
        second.transition(
            Transition(
                incident_id=incident.incident_id,
                target=IncidentStatus.INVESTIGATING,
                expected_revision=incident.revision,
                actor="second",
                reason="Start",
            )
        )
        with pytest.raises(Conflict):
            first.transition(
                Transition(
                    incident_id=incident.incident_id,
                    target=IncidentStatus.INVESTIGATING,
                    expected_revision=incident.revision,
                    actor="first",
                    reason="Stale",
                )
            )
        assert len(first.audit(incident.incident_id)) == 3


def test_locked_database_is_reported_and_recovers(path, record):
    with SQLiteRepository(path, timeout=0.0) as repo, closing(sqlite3.connect(path)) as blocker:
        blocker.execute("BEGIN IMMEDIATE")
        with pytest.raises(StorageBusy):
            repo.save(record)
        blocker.rollback()
        assert repo.save(record) == record


def test_model_construct_cannot_bypass_storage_validation(path, record):
    wrong = record.result.model_copy(update={"incident_id": "INC-wrong"})
    with SQLiteRepository(path) as repo, pytest.raises(ValidationError):
        repo.save(record.model_copy(update={"result": wrong}))


def test_blocked_analysis_is_preserved_without_fabricated_report(path, request_factory):
    from canovatwin.policy import Policy

    with SQLiteRepository(path, create=True) as repo:
        record = HistoryService(repo).analyze(request_factory(), policy=Policy(max_agents=1))
        loaded = repo.get_run(record.run_id)
        assert loaded.result.status == "blocked" and loaded.result.report is None
        assert repo.list_runs(record.result.incident_id)[0].report_status is None


@pytest.mark.parametrize(
    "change", [dict(actor=" "), dict(recorded_at=datetime(2026, 10, 28)), dict(replay_of="self")]
)
def test_record_metadata_validation(record, change):
    if change.get("replay_of") == "self":
        change["replay_of"] = record.run_id
    with pytest.raises(ValidationError):
        RecordedAnalysis.model_validate(record.model_dump() | change)


def test_timestamp_is_normalized_to_utc(record):
    from datetime import timedelta, timezone

    record = RecordedAnalysis.model_validate(
        record.model_dump() | {"recorded_at": datetime(2026, 10, 28, 3, tzinfo=timezone(timedelta(hours=3)))}
    )
    assert record.recorded_at == datetime(2026, 10, 28, tzinfo=UTC)


@pytest.mark.parametrize(
    ("column", "value"), [("payload", b"blob"), ("checksum", b"blob"), ("checksum", "ş")]
)
def test_invalid_payload_types_are_reported_as_corruption(path, record, column, value):
    execute(path, f"UPDATE analysis_runs SET {column}=?", (value,))
    with SQLiteRepository(path) as repo, pytest.raises(CorruptRecord):
        repo.get_run(record.run_id)


def test_invalid_metadata_types_are_reported_as_corruption(path, record):
    execute(path, "UPDATE incidents SET asset_id=?", (b"blob",))
    with SQLiteRepository(path) as repo:
        with pytest.raises(CorruptRecord):
            repo.list_incidents()
        with pytest.raises(CorruptRecord):
            HistoryService(repo).analyze(record.request)


def test_existing_empty_database_requires_explicit_initialization(path):
    path.touch()
    with pytest.raises(UnsupportedSchema):
        SQLiteRepository(path)
    assert path.read_bytes() == b""
    with SQLiteRepository(path, create=True) as repo:
        assert repo.list_incidents() == ()


def test_unverified_or_incoherent_history_is_rejected(path, record):
    mutations = [
        {"report": record.result.report.model_copy(update={"summary": "Unverified"})},
        {"total_tool_calls": 999},
        {"outputs": record.result.outputs[:-1]},
        {
            "trace": (record.result.trace[0].model_copy(update={"status": "failed"}),)
            + record.result.trace[1:]
        },
    ]
    with SQLiteRepository(path) as repo:
        for change in mutations:
            altered = record.model_copy(
                update={"run_id": "RUN-altered", "result": record.result.model_copy(update=change)}
            )
            with pytest.raises(ValidationError):
                repo.save(altered)
        assert repo.get_incident(record.result.incident_id).run_count == 1
