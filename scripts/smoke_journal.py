"""Verify durable stream recovery from an installed wheel."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from canovatwin.stream import StreamConfig
from canovatwin.stream_journal import StreamJournal
from canovatwin.telemetry import generate_case


def main() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    points = generate_case(count=30, start=start).window.samples
    config = StreamConfig(asset_id="journal-smoke", max_lateness_s=0)
    with TemporaryDirectory() as directory:
        path = Path(directory) / "stream.sqlite3"
        with StreamJournal(path, config, create=True) as journal:
            for point in points[:3]:
                journal.append(point, received_at=point.timestamp)
                journal.drain(as_of=point.timestamp)
            journal.disconnect(at=start + timedelta(seconds=3))
        with StreamJournal(path, config) as restored:
            assert restored.event_count == 7
            assert restored.window(count=3).samples == points[:3]
            assert restored.state(as_of=start + timedelta(seconds=3)).connection == "disconnected"
    print("Installed stream journal: durable recovery, window and connection passed")


if __name__ == "__main__":
    main()
