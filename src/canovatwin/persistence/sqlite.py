"""Transactional SQLite repository for local, synthetic-only analysis history."""

import json
import math
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from hashlib import sha256
from hmac import compare_digest
from pathlib import Path

from pydantic import ValidationError

from ..assets import AssetRollup
from ..contracts import Contract
from .errors import (
    Conflict,
    CorruptRecord,
    InvalidTransition,
    NotFound,
    StorageBusy,
    StorageError,
    UnsupportedSchema,
)
from .models import AuditEvent, IncidentStatus, IncidentSummary, RecordedAnalysis, RunSummary, Transition
from .schema import APPLICATION_ID, SCHEMA_VERSION, STATEMENTS, TABLES

_TRANSITIONS = {
    IncidentStatus.OPEN: frozenset({IncidentStatus.INVESTIGATING}),
    IncidentStatus.INVESTIGATING: frozenset({IncidentStatus.OPEN, IncidentStatus.CLOSED}),
    IncidentStatus.CLOSED: frozenset({IncidentStatus.OPEN}),
}
_SUMMARY_SQL = """SELECT i.*, (SELECT COUNT(*) FROM analysis_runs a WHERE a.incident_id=i.incident_id) AS run_count,
    r.run_id AS latest_run_id, r.status AS latest_analysis_status, r.report_status AS latest_report_status
    FROM incidents i JOIN analysis_runs r ON r.sequence =
    (SELECT MAX(a.sequence) FROM analysis_runs a WHERE a.incident_id=i.incident_id)"""


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _checksum(payload: str) -> str:
    return sha256(payload.encode("utf-8")).hexdigest()


def _decode[Model: Contract](model: type[Model], payload: str) -> Model:
    try:
        return model.model_validate_json(payload)
    except (ValidationError, ValueError, TypeError):
        raise CorruptRecord("Stored data does not match its declared schema") from None


def _decode_row[Model: Contract](model: type[Model], row: sqlite3.Row) -> Model:
    try:
        payload = json.dumps(dict(row))
    except (TypeError, ValueError):
        raise CorruptRecord("Stored metadata contains an unsupported value type") from None
    return _decode(model, payload)


def _page(limit: int, offset: int) -> None:
    if type(limit) is not int or not 1 <= limit <= 100 or type(offset) is not int or offset < 0:
        raise ValueError("Pagination requires limit 1–100 and a nonnegative offset")


class SQLiteRepository:
    def __init__(
        self,
        path: Path,
        *,
        create: bool = False,
        read_only: bool = False,
        timeout: float = 5.0,
        clock: Callable[[], datetime] = _utc_now,
    ):
        if not math.isfinite(timeout) or timeout < 0:
            raise ValueError("timeout must be finite and nonnegative")
        if read_only and create:
            raise ValueError("A read-only connection cannot create a database")
        self._read_only = read_only
        self._allow_initialize = create
        self._clock = clock
        self._closed = False
        path = Path(path).resolve()
        if not create and not path.is_file():
            raise NotFound("History database does not exist")
        mode = "ro" if read_only else "rwc" if create else "rw"
        try:
            if create:
                path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(
                f"{path.as_uri()}?mode={mode}", uri=True, timeout=timeout, isolation_level=None
            )
        except (sqlite3.Error, OSError):
            raise StorageError("Cannot open the history database") from None
        self._connection.row_factory = sqlite3.Row
        try:
            self._execute("PRAGMA foreign_keys=ON")
            self._initialize()
        except BaseException:
            self.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self) -> None:
        if not self._closed:
            self._connection.close()
            self._closed = True

    def _execute(self, sql: str, parameters: tuple = ()) -> sqlite3.Cursor:
        try:
            return self._connection.execute(sql, parameters)
        except sqlite3.Error as exc:
            if getattr(exc, "sqlite_errorcode", None) in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
                raise StorageBusy("History database is busy; retry after the other writer finishes") from None
            raise StorageError("History database operation failed") from None

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        if self._read_only:
            raise StorageError("History connection is read-only")
        self._execute("BEGIN IMMEDIATE")
        try:
            yield
            self._execute("COMMIT")
        except BaseException:
            if self._connection.in_transaction:
                self._connection.rollback()
            raise

    def _initialize(self) -> None:
        version = self._execute("PRAGMA user_version").fetchone()[0]
        application = self._execute("PRAGMA application_id").fetchone()[0]
        if version == 0 and application == 0 and self._allow_initialize:
            # Re-read under the write lock: another process may initialize first.
            with self._transaction():
                version = self._execute("PRAGMA user_version").fetchone()[0]
                application = self._execute("PRAGMA application_id").fetchone()[0]
                if version == 0 and application == 0:
                    existing = self._execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    ).fetchall()
                    if existing:
                        raise UnsupportedSchema("An unrelated database will not be initialized")
                    for statement in STATEMENTS:
                        self._execute(statement)
                    self._execute(f"PRAGMA application_id={APPLICATION_ID}")
                    self._execute(f"PRAGMA user_version={SCHEMA_VERSION}")
                    version, application = SCHEMA_VERSION, APPLICATION_ID
        if version != SCHEMA_VERSION or application != APPLICATION_ID:
            raise UnsupportedSchema("History database version or application identifier is unsupported")
        existing = {
            row[0] for row in self._execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        if not TABLES <= existing:
            raise CorruptRecord("History schema is incomplete")

    def save(self, record: RecordedAnalysis) -> RecordedAnalysis:
        record = RecordedAnalysis.model_validate(record.model_dump())
        payload = record.model_dump_json()
        incident_id = record.result.incident_id
        recorded_at = record.recorded_at.isoformat()
        with self._transaction():
            existing = self._execute(
                "SELECT run_id FROM analysis_runs WHERE run_id=?", (record.run_id,)
            ).fetchone()
            if existing:
                stored = self.get_run(record.run_id)
                if stored != record:
                    raise Conflict("Run ID already belongs to another immutable record")
                return stored
            if record.replay_of:
                source = self.get_run(record.replay_of)
                if source.request != record.request or source.policy != record.policy:
                    raise Conflict("Replay must retain its original request and policy")
            incident = self._execute("SELECT * FROM incidents WHERE incident_id=?", (incident_id,)).fetchone()
            if incident is None:
                revision = 1
                self._execute(
                    "INSERT INTO incidents VALUES (?, ?, 'open', ?, ?, ?)",
                    (incident_id, record.request.window.asset_id, revision, recorded_at, recorded_at),
                )
                self._audit(
                    incident_id,
                    None,
                    recorded_at,
                    record.actor,
                    "incident_created",
                    None,
                    IncidentStatus.OPEN,
                    "Analysis window recorded",
                    revision,
                )
            else:
                summary = self.get_incident(incident_id)
                if summary.asset_id != record.request.window.asset_id:
                    raise CorruptRecord("Incident asset does not match the recorded request")
                revision = summary.revision + 1
                updated_at = max(summary.updated_at.isoformat(), recorded_at)
                self._execute(
                    "UPDATE incidents SET revision=?, updated_at=? WHERE incident_id=?",
                    (revision, updated_at, incident_id),
                )
            self._execute(
                """INSERT INTO analysis_runs
                (run_id, incident_id, recorded_at, engine_version, status, report_status, replay_of, payload, checksum)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.run_id,
                    incident_id,
                    recorded_at,
                    record.engine_version,
                    record.result.status,
                    record.result.report.status if record.result.report else None,
                    record.replay_of,
                    payload,
                    _checksum(payload),
                ),
            )
            for ordinal, evidence in enumerate(record.result.evidence):
                self._execute(
                    "INSERT INTO evidence VALUES (?, ?, ?, ?)",
                    (record.run_id, ordinal, evidence.evidence_id, evidence.model_dump_json()),
                )
            for ordinal, trace in enumerate(record.result.trace):
                self._execute(
                    "INSERT INTO agent_runs VALUES (?, ?, ?, ?)",
                    (record.run_id, ordinal, trace.task_id, trace.model_dump_json()),
                )
            self._audit(
                incident_id,
                record.run_id,
                recorded_at,
                record.actor,
                "analysis_saved",
                None,
                None,
                "Historical replay saved" if record.replay_of else "Analysis result saved",
                revision,
            )
        return record

    def get_run(self, run_id: str) -> RecordedAnalysis:
        row = self._execute("SELECT * FROM analysis_runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None:
            raise NotFound("Analysis run was not found")
        if (
            not isinstance(row["payload"], str)
            or not isinstance(row["checksum"], str)
            or not row["checksum"].isascii()
        ):
            raise CorruptRecord("Analysis payload or checksum has an invalid type or encoding")
        if not compare_digest(_checksum(row["payload"]), row["checksum"]):
            raise CorruptRecord("Analysis payload checksum does not match")
        record = _decode(RecordedAnalysis, row["payload"])
        expected = (
            record.run_id,
            record.result.incident_id,
            record.recorded_at.isoformat(),
            record.engine_version,
            record.result.status,
            record.result.report.status if record.result.report else None,
            record.replay_of,
        )
        actual = tuple(
            row[key]
            for key in (
                "run_id",
                "incident_id",
                "recorded_at",
                "engine_version",
                "status",
                "report_status",
                "replay_of",
            )
        )
        if actual != expected:
            raise CorruptRecord("Analysis metadata does not match its payload")
        for table, id_field, records in (
            ("evidence", "evidence_id", record.result.evidence),
            ("agent_runs", "task_id", record.result.trace),
        ):
            # table and field are hardcoded internal identifiers, never supplied by a caller.
            stored = self._execute(
                f"SELECT ordinal, {id_field}, payload FROM {table} WHERE run_id=? ORDER BY ordinal", (run_id,)
            ).fetchall()
            expected_rows = [
                (i, getattr(item, id_field), item.model_dump_json()) for i, item in enumerate(records)
            ]
            if [tuple(item) for item in stored] != expected_rows:
                raise CorruptRecord("Analysis detail records disagree with their source payload")
        return record

    def get_incident(self, incident_id: str) -> IncidentSummary:
        row = self._execute(_SUMMARY_SQL + " WHERE i.incident_id=?", (incident_id,)).fetchone()
        if row is None:
            raise NotFound("Incident was not found")
        return _decode_row(IncidentSummary, row)

    def list_incidents(
        self,
        *,
        status: IncidentStatus | None = None,
        limit: int = 20,
        offset: int = 0,
        asset_id: str | None = None,
    ) -> tuple[IncidentSummary, ...]:
        _page(limit, offset)
        if status is not None and not isinstance(status, IncidentStatus):
            raise ValueError("status must be an IncidentStatus")
        filters = []
        parameters = []
        if status is not None:
            filters.append("i.status=?")
            parameters.append(status.value)
        if asset_id is not None:
            if not isinstance(asset_id, str) or not 1 <= len(asset_id) <= 100:
                raise ValueError("Invalid asset identifier")
            filters.append("i.asset_id=?")
            parameters.append(asset_id)
        where = " WHERE " + " AND ".join(filters) if filters else ""
        rows = self._execute(
            _SUMMARY_SQL + where + " ORDER BY r.sequence DESC LIMIT ? OFFSET ?",
            tuple(parameters + [limit, offset]),
        ).fetchall()
        return tuple(_decode_row(IncidentSummary, row) for row in rows)

    def asset_inventory(
        self,
        configured_ids: tuple[str, ...],
        *,
        asset_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
        configured_only: bool = False,
    ) -> tuple[AssetRollup, ...]:
        _page(limit, offset)
        if not 1 <= len(configured_ids) <= 100 or any(
            not isinstance(value, str) or not 1 <= len(value) <= 100 for value in configured_ids
        ):
            raise ValueError("Expected 1–100 configured asset identifiers")
        if asset_id is not None and (not isinstance(asset_id, str) or not 1 <= len(asset_id) <= 100):
            raise ValueError("Invalid asset identifier")
        values = ",".join("(?)" for _ in configured_ids)
        observed = "" if configured_only else " UNION SELECT asset_id FROM incidents"
        sql = f"""WITH configured(asset_id) AS (VALUES {values}),
            assets AS (SELECT asset_id FROM configured{observed}),
            incident_stats AS (
                SELECT asset_id, count(*) AS incident_count,
                    sum(CASE WHEN status!='closed' THEN 1 ELSE 0 END) AS open_incident_count
                FROM incidents GROUP BY asset_id),
            run_stats AS (
                SELECT i.asset_id, count(*) AS run_count, max(r.sequence) AS latest_sequence
                FROM analysis_runs r JOIN incidents i ON i.incident_id=r.incident_id GROUP BY i.asset_id)
            SELECT a.asset_id, coalesce(i.incident_count,0) AS incident_count,
                coalesce(i.open_incident_count,0) AS open_incident_count,
                coalesce(s.run_count,0) AS run_count,
                r.run_id AS latest_run_id, r.recorded_at AS last_recorded_at
            FROM assets a LEFT JOIN incident_stats i ON i.asset_id=a.asset_id
            LEFT JOIN run_stats s ON s.asset_id=a.asset_id
            LEFT JOIN analysis_runs r ON r.sequence=s.latest_sequence"""
        parameters = list(configured_ids)
        if asset_id is not None:
            sql += " WHERE a.asset_id=?"
            parameters.append(asset_id)
        rows = self._execute(
            sql + " ORDER BY a.asset_id LIMIT ? OFFSET ?", tuple(parameters + [limit, offset])
        ).fetchall()
        return tuple(_decode_row(AssetRollup, row) for row in rows)

    def list_runs(self, incident_id: str, *, limit: int = 20, offset: int = 0) -> tuple[RunSummary, ...]:
        _page(limit, offset)
        self.get_incident(incident_id)
        rows = self._execute(
            """SELECT run_id, incident_id, recorded_at, engine_version, status, report_status, replay_of
            FROM analysis_runs WHERE incident_id=? ORDER BY sequence DESC LIMIT ? OFFSET ?""",
            (incident_id, limit, offset),
        ).fetchall()
        return tuple(_decode_row(RunSummary, row) for row in rows)

    def transition(self, change: Transition) -> IncidentSummary:
        change = Transition.model_validate(change.model_dump())
        now = self._clock()
        if now.utcoffset() is None:
            raise ValueError("Repository clock must include a timezone")
        timestamp = now.astimezone(UTC).isoformat()
        with self._transaction():
            current = self.get_incident(change.incident_id)
            if current.revision != change.expected_revision:
                raise Conflict("Incident changed; reload its latest revision before retrying")
            if change.target not in _TRANSITIONS[current.status]:
                raise InvalidTransition("Requested incident lifecycle transition is not allowed")
            revision = current.revision + 1
            self._execute(
                "UPDATE incidents SET status=?, revision=?, updated_at=? WHERE incident_id=?",
                (
                    change.target.value,
                    revision,
                    max(current.updated_at.isoformat(), timestamp),
                    change.incident_id,
                ),
            )
            self._audit(
                change.incident_id,
                None,
                timestamp,
                change.actor,
                "status_changed",
                current.status,
                change.target,
                change.reason,
                revision,
            )
            updated = self.get_incident(change.incident_id)
        return updated

    def _audit(
        self,
        incident_id: str,
        run_id: str | None,
        recorded_at: str,
        actor: str,
        action: str,
        old_status: IncidentStatus | None,
        new_status: IncidentStatus | None,
        reason: str,
        revision: int,
    ) -> None:
        self._execute(
            """INSERT INTO audit_events
            (incident_id, run_id, recorded_at, actor, action, old_status, new_status, reason, revision)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                incident_id,
                run_id,
                recorded_at,
                actor,
                action,
                old_status.value if old_status else None,
                new_status.value if new_status else None,
                reason,
                revision,
            ),
        )

    def audit(self, incident_id: str, *, limit: int = 20, offset: int = 0) -> tuple[AuditEvent, ...]:
        _page(limit, offset)
        self.get_incident(incident_id)
        rows = self._execute(
            "SELECT * FROM audit_events WHERE incident_id=? ORDER BY event_id DESC LIMIT ? OFFSET ?",
            (incident_id, limit, offset),
        ).fetchall()
        return tuple(_decode_row(AuditEvent, row) for row in rows)
