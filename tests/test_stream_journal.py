"""Durability, recovery, corruption and concurrency tests for offline replay."""

import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from canovatwin.stream import StreamConfig
from canovatwin.stream_journal import ConcurrentJournal, CorruptJournal, JournalError, StreamJournal
from canovatwin.telemetry import generate_case

START = datetime(2026, 1, 1, tzinfo=UTC)
CONFIG = StreamConfig(asset_id="rack-a", max_lateness_s=2)


def points():
    return generate_case(count=30, start=START).window.samples


def test_reopen_recovers_pending_watermark_connection_and_window(tmp_path):
    path = tmp_path / "stream.sqlite3"
    p = points()
    with StreamJournal(path, CONFIG, create=True) as journal:
        for index in (2, 0, 1):
            journal.append(p[index], received_at=START + timedelta(seconds=3))
        assert journal.drain(as_of=START + timedelta(seconds=3)) == p[:2]
        journal.disconnect(at=START + timedelta(seconds=4))
        assert journal.event_count == 5
    with StreamJournal(path, CONFIG) as restored:
        state = restored.state(as_of=START + timedelta(seconds=4))
        assert (state.connection, state.pending, state.committed) == ("disconnected", 1, 2)
        assert state.watermark_at == START + timedelta(seconds=1)
        restored.reconnect(at=START + timedelta(seconds=5))
        assert restored.drain(as_of=START + timedelta(seconds=5)) == (p[2],)
        assert restored.window(count=3).samples == p[:3]
    with StreamJournal(path, CONFIG) as again:
        assert again.window(count=3).samples == p[:3]
        assert again.event_count == 7


def test_rejected_event_does_not_change_disk_or_live_state(tmp_path):
    path = tmp_path / "stream.sqlite3"
    with StreamJournal(path, CONFIG, create=True) as journal:
        journal.append(points()[0], received_at=START)
        with pytest.raises(ValueError, match="Duplicate"):
            journal.append(points()[0], received_at=START)
        assert journal.event_count == 1
        assert journal.state(as_of=START).pending == 1
    with StreamJournal(path, CONFIG) as restored:
        assert restored.event_count == 1
        assert restored.state(as_of=START).pending == 1


def test_two_writers_fail_closed_instead_of_losing_updates(tmp_path):
    path = tmp_path / "stream.sqlite3"
    with StreamJournal(path, CONFIG, create=True) as first, StreamJournal(path, CONFIG) as second:
        first.append(points()[0], received_at=START)
        with pytest.raises(ConcurrentJournal):
            second.append(points()[1], received_at=START + timedelta(seconds=1))
        assert second.event_count == 0
    with StreamJournal(path, CONFIG) as restored:
        assert restored.event_count == 1


@pytest.mark.parametrize("column,value", [("payload", "{}"), ("digest", "f" * 64)])
def test_modified_event_is_rejected_on_reopen(tmp_path, column, value):
    path = tmp_path / "stream.sqlite3"
    with StreamJournal(path, CONFIG, create=True) as journal:
        journal.append(points()[0], received_at=START)
    with sqlite3.connect(path) as db:
        db.execute(f"UPDATE stream_events SET {column}=? WHERE sequence=1", (value,))
    db.close()
    with pytest.raises(CorruptJournal):
        StreamJournal(path, CONFIG)


def test_deleted_tail_is_detected_from_metadata(tmp_path):
    path = tmp_path / "stream.sqlite3"
    with StreamJournal(path, CONFIG, create=True) as journal:
        journal.append(points()[0], received_at=START)
    with sqlite3.connect(path) as db:
        db.execute("DELETE FROM stream_events WHERE sequence=1")
    db.close()
    with pytest.raises(CorruptJournal, match="head or event count"):
        StreamJournal(path, CONFIG)


def test_wrong_config_and_unrelated_database_are_rejected(tmp_path):
    path = tmp_path / "stream.sqlite3"
    with StreamJournal(path, CONFIG, create=True):
        pass
    with pytest.raises(CorruptJournal, match="configuration"):
        StreamJournal(path, StreamConfig(asset_id="other"))
    unrelated = tmp_path / "unrelated.sqlite3"
    with sqlite3.connect(unrelated) as db:
        db.execute("CREATE TABLE records (id INTEGER)")
    db.close()
    with pytest.raises(CorruptJournal, match="unrelated"):
        StreamJournal(unrelated, CONFIG, create=True)
    with sqlite3.connect(unrelated) as db:
        assert db.execute("SELECT name FROM sqlite_master WHERE name='records'").fetchone()
    db.close()


def test_missing_file_and_declared_capacity_fail_explicitly(tmp_path, monkeypatch):
    path = tmp_path / "stream.sqlite3"
    with pytest.raises(JournalError, match="does not exist"):
        StreamJournal(path, CONFIG)
    with StreamJournal(path, CONFIG, create=True) as journal:
        monkeypatch.setattr("canovatwin.stream_journal.MAX_EVENTS", 0)
        with pytest.raises(JournalError, match="limit"):
            journal.append(points()[0], received_at=START)
        assert journal.event_count == 0


def test_sqlite_write_failure_rolls_back_without_advancing_live_state(tmp_path):
    path = tmp_path / "stream.sqlite3"
    with StreamJournal(path, CONFIG, create=True) as journal:
        with sqlite3.connect(path) as db:
            db.execute(
                "CREATE TRIGGER reject_stream_event BEFORE INSERT ON stream_events "
                "BEGIN SELECT RAISE(ABORT, 'test failure'); END"
            )
        db.close()
        with pytest.raises(JournalError, match="write failed"):
            journal.append(points()[0], received_at=START)
        assert journal.event_count == 0
        assert journal.state(as_of=START).pending == 0
    with StreamJournal(path, CONFIG) as restored:
        assert restored.event_count == 0
