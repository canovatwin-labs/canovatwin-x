"""Transactional, bounded replay journal for the offline stream collector."""

import json
import sqlite3
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
from hmac import compare_digest
from pathlib import Path
from typing import Literal

from pydantic import ValidationError

from .contracts import SensorSample, TelemetryWindow
from .stream import StreamCollector, StreamConfig, StreamState

APPLICATION_ID = 0x43545853  # CTXS; deliberately distinct from analysis history.
SCHEMA_VERSION = 1
GENESIS = "0" * 64
MAX_EVENTS = 10_000
Kind = Literal["append", "drain", "disconnect", "reconnect"]


class JournalError(RuntimeError):
    """The journal could not be used without risking an inconsistent stream."""


class CorruptJournal(JournalError):
    """Stored event sequence, hash chain, schema or replay is invalid."""


class ConcurrentJournal(JournalError):
    """Another writer changed the journal after this handle was opened."""


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash(sequence: int, kind: str, payload: str, previous: str) -> str:
    return sha256(_json([sequence, kind, payload, previous]).encode()).hexdigest()


class StreamJournal:
    """Apply each event to a clone, commit it, then publish the new state.

    A failed SQLite transaction leaves the live collector unchanged. Recovery
    verifies the complete chain and replays every event against domain rules.
    """

    def __init__(self, path: Path, config: StreamConfig, *, create: bool = False):
        self._config = StreamConfig.model_validate(config.model_dump())
        path = Path(path).resolve()
        if not create and not path.is_file():
            raise JournalError("Stream journal does not exist")
        if create:
            path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._db = sqlite3.connect(
                f"{path.as_uri()}?mode={'rwc' if create else 'rw'}",
                uri=True,
                timeout=5,
                isolation_level=None,
            )
            self._db.row_factory = sqlite3.Row
            self._db.execute("PRAGMA synchronous=FULL")
            self._initialize(create)
            self._db.execute("BEGIN")
            try:
                self._collector, self._count, self._head = self._recover()
                self._db.execute("COMMIT")
            except BaseException:
                self._db.rollback()
                raise
        except BaseException as exc:
            if hasattr(self, "_db"):
                self._db.close()
            if isinstance(exc, sqlite3.Error):
                raise JournalError("Cannot open or inspect the stream journal") from exc
            raise

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self) -> None:
        self._db.close()

    def _initialize(self, create: bool) -> None:
        application = self._db.execute("PRAGMA application_id").fetchone()[0]
        version = self._db.execute("PRAGMA user_version").fetchone()[0]
        if (application, version) == (0, 0) and create:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                application = self._db.execute("PRAGMA application_id").fetchone()[0]
                version = self._db.execute("PRAGMA user_version").fetchone()[0]
                if (application, version) == (0, 0):
                    if self._db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]:
                        raise CorruptJournal("Refusing to initialize an unrelated database")
                    self._db.execute(
                        "CREATE TABLE stream_meta (id INTEGER PRIMARY KEY CHECK(id=1), "
                        "config TEXT NOT NULL, count INTEGER NOT NULL, head TEXT NOT NULL)"
                    )
                    self._db.execute(
                        "CREATE TABLE stream_events (sequence INTEGER PRIMARY KEY, kind TEXT NOT NULL, "
                        "payload TEXT NOT NULL, previous TEXT NOT NULL, digest TEXT NOT NULL)"
                    )
                    self._db.execute(
                        "INSERT INTO stream_meta VALUES (1, ?, 0, ?)",
                        (_json(self._config.model_dump(mode="json")), GENESIS),
                    )
                    self._db.execute(f"PRAGMA application_id={APPLICATION_ID}")
                    self._db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
                self._db.execute("COMMIT")
            except BaseException:
                self._db.rollback()
                raise
            application, version = APPLICATION_ID, SCHEMA_VERSION
        if (application, version) != (APPLICATION_ID, SCHEMA_VERSION):
            raise CorruptJournal("Unsupported stream journal schema")
        tables = {
            row[0] for row in self._db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if not {"stream_meta", "stream_events"} <= tables:
            raise CorruptJournal("Stream journal schema is incomplete")

    @staticmethod
    def _replay(collector: StreamCollector, kind: Kind, payload: dict):
        if kind == "append":
            if set(payload) != {"sample", "received_at"}:
                raise CorruptJournal("Append event has unexpected fields")
            collector.append(
                SensorSample.model_validate_json(_json(payload["sample"])),
                received_at=datetime.fromisoformat(payload["received_at"]),
            )
            return None
        if kind == "drain":
            if set(payload) != {"as_of"}:
                raise CorruptJournal("Drain event has unexpected fields")
            return collector.drain(as_of=datetime.fromisoformat(payload["as_of"]))
        if kind == "disconnect":
            if set(payload) != {"at"}:
                raise CorruptJournal("Disconnect event has unexpected fields")
            collector.disconnect(at=datetime.fromisoformat(payload["at"]))
            return None
        if kind == "reconnect":
            if set(payload) != {"at"}:
                raise CorruptJournal("Reconnect event has unexpected fields")
            collector.reconnect(at=datetime.fromisoformat(payload["at"]))
            return None
        raise CorruptJournal("Unknown journal event")

    def _recover(self) -> tuple[StreamCollector, int, str]:
        rows = self._db.execute("SELECT config, count, head FROM stream_meta WHERE id=1").fetchall()
        if len(rows) != 1 or rows[0]["config"] != _json(self._config.model_dump(mode="json")):
            raise CorruptJournal("Stream configuration is missing or differs from the journal")
        if type(rows[0]["count"]) is not int or not isinstance(rows[0]["head"], str):
            raise CorruptJournal("Stream journal metadata has invalid types")
        collector = StreamCollector(self._config)
        head = GENESIS
        count = 0
        try:
            for row in self._db.execute(
                "SELECT sequence, kind, payload, previous, digest FROM stream_events ORDER BY sequence"
            ):
                count += 1
                if count > MAX_EVENTS or row["sequence"] != count or row["previous"] != head:
                    raise CorruptJournal("Stream event sequence or chain is broken")
                expected = _hash(count, row["kind"], row["payload"], head)
                if not compare_digest(expected, row["digest"]):
                    raise CorruptJournal("Stream event checksum mismatch")
                payload = json.loads(row["payload"])
                if not isinstance(payload, dict):
                    raise CorruptJournal("Stream event payload is not an object")
                self._replay(collector, row["kind"], payload)
                head = expected
        except (ValueError, KeyError, TypeError, ValidationError, sqlite3.Error) as exc:
            raise CorruptJournal("Stream event cannot be replayed") from exc
        if rows[0]["count"] != count or not compare_digest(rows[0]["head"], head):
            raise CorruptJournal("Stream journal head or event count is inconsistent")
        return collector, count, head

    def _apply(self, kind: Kind, payload: dict):
        if self._count >= MAX_EVENTS:
            raise JournalError("Stream journal reached its declared 10000-event limit")
        candidate = deepcopy(self._collector)
        result = self._replay(candidate, kind, payload)
        serialized = _json(payload)
        sequence = self._count + 1
        digest = _hash(sequence, kind, serialized, self._head)
        try:
            self._db.execute("BEGIN IMMEDIATE")
            row = self._db.execute("SELECT count, head FROM stream_meta WHERE id=1").fetchone()
            if row is None or row["count"] != self._count or row["head"] != self._head:
                raise ConcurrentJournal("Stream journal changed in another writer")
            self._db.execute(
                "INSERT INTO stream_events VALUES (?, ?, ?, ?, ?)",
                (sequence, kind, serialized, self._head, digest),
            )
            self._db.execute("UPDATE stream_meta SET count=?, head=? WHERE id=1", (sequence, digest))
            self._db.execute("COMMIT")
        except BaseException as exc:
            if self._db.in_transaction:
                self._db.rollback()
            if isinstance(exc, JournalError):
                raise
            if isinstance(exc, sqlite3.Error):
                raise JournalError("Stream journal write failed; live state was not advanced") from exc
            raise
        self._collector, self._count, self._head = candidate, sequence, digest
        return result

    def append(self, sample: SensorSample, *, received_at: datetime) -> None:
        self._apply(
            "append", {"sample": sample.model_dump(mode="json"), "received_at": received_at.isoformat()}
        )

    def drain(self, *, as_of: datetime) -> tuple[SensorSample, ...]:
        return self._apply("drain", {"as_of": as_of.isoformat()})

    def disconnect(self, *, at: datetime) -> None:
        self._apply("disconnect", {"at": at.isoformat()})

    def reconnect(self, *, at: datetime) -> None:
        self._apply("reconnect", {"at": at.isoformat()})

    def state(self, *, as_of: datetime) -> StreamState:
        return self._collector.state(as_of=as_of)

    def window(self, *, count: int) -> TelemetryWindow:
        return self._collector.window(count=count)

    @property
    def event_count(self) -> int:
        return self._count
