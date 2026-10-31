"""Exercise the public stream contract from an installed, isolated wheel."""

from datetime import UTC, datetime, timedelta

from canovatwin.stream import StreamCollector, StreamConfig
from canovatwin.telemetry import generate_case


def main() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    points = generate_case(count=30, start=start).window.samples
    stream = StreamCollector(StreamConfig(asset_id="package-smoke", max_lateness_s=2))
    for index in (2, 0, 1):
        stream.append(points[index], received_at=start + timedelta(seconds=3))
    assert stream.drain(as_of=start + timedelta(seconds=4)) == points[:3]
    assert stream.window(count=3).asset_id == "package-smoke"
    assert stream.state(as_of=start + timedelta(seconds=4)).freshness == "fresh"
    assert stream.state(as_of=start + timedelta(seconds=4)).watermark_at == start + timedelta(seconds=2)
    print("Installed stream contract: event-time ordering, window and freshness passed")


if __name__ == "__main__":
    main()
