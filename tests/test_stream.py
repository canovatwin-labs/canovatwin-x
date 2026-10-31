"""Event-time ordering, backpressure and connection-state regression tests."""

from datetime import UTC, datetime, timedelta

import pytest

from canovatwin.stream import StreamCollector, StreamConfig
from canovatwin.telemetry import generate_case

START = datetime(2026, 1, 1, tzinfo=UTC)


def samples():
    return generate_case(count=30, start=START).window.samples


def collector(**kwargs):
    return StreamCollector(StreamConfig(asset_id="rack-a", **kwargs))


def test_out_of_order_arrival_is_committed_in_measurement_order():
    stream = collector(max_lateness_s=2)
    points = samples()
    for index in (2, 0, 1):
        stream.append(points[index], received_at=START + timedelta(seconds=3))
    assert stream.drain(as_of=START + timedelta(seconds=3)) == (points[0], points[1])
    assert stream.state(as_of=START + timedelta(seconds=3)).pending == 1
    assert stream.drain(as_of=START + timedelta(seconds=4)) == (points[2],)
    assert stream.window(count=3).samples == points[:3]


def test_late_duplicate_and_replayed_timestamp_fail_closed():
    stream = collector(max_lateness_s=0)
    points = samples()
    stream.append(points[0], received_at=START)
    with pytest.raises(ValueError, match="Duplicate sample ID"):
        stream.append(points[0], received_at=START)
    stream.drain(as_of=START)
    with pytest.raises(ValueError, match="watermark"):
        stream.append(points[0], received_at=START + timedelta(seconds=1))


def test_bounded_buffer_requires_explicit_drain():
    stream = collector(max_lateness_s=300, max_pending=3)
    points = samples()
    for point in points[:3]:
        stream.append(point, received_at=START + timedelta(seconds=3))
    with pytest.raises(ValueError, match="buffer is full"):
        stream.append(points[3], received_at=START + timedelta(seconds=3))
    assert stream.state(as_of=START + timedelta(seconds=3)).pending == 3
    assert not stream.drain(as_of=START + timedelta(seconds=3))


def test_disconnect_reconnect_and_stale_state_are_explicit():
    stream = collector(max_lateness_s=0, stale_after_s=5)
    point = samples()[0]
    assert stream.state(as_of=START).freshness == "empty"
    stream.append(point, received_at=START)
    stream.drain(as_of=START)
    assert stream.state(as_of=START).freshness == "fresh"
    stream.disconnect(at=START + timedelta(seconds=1))
    state = stream.state(as_of=START + timedelta(seconds=1))
    assert (state.connection, state.freshness) == ("disconnected", "stale")
    with pytest.raises(ValueError, match="disconnected"):
        stream.append(samples()[1], received_at=START + timedelta(seconds=2))
    stream.reconnect(at=START + timedelta(seconds=3))
    assert stream.state(as_of=START + timedelta(seconds=6)).freshness == "stale"


def test_clock_guards_do_not_mutate_state_on_rejection():
    stream = collector()
    point = samples()[0]
    with pytest.raises(ValueError, match="timezone"):
        stream.append(point, received_at=START.replace(tzinfo=None))
    with pytest.raises(ValueError, match="future"):
        stream.append(point, received_at=START - timedelta(seconds=10))
    assert stream.state(as_of=START).pending == 0
    stream.append(point, received_at=START)
    with pytest.raises(ValueError, match="backwards"):
        stream.disconnect(at=START - timedelta(seconds=1))
    assert stream.state(as_of=START).connection == "connected"


def test_window_requires_committed_minimum_and_retains_bounded_history():
    stream = collector(max_lateness_s=0)
    with pytest.raises(ValueError, match="Not enough"):
        stream.window(count=3)
    with pytest.raises(ValueError, match="integer"):
        stream.window(count=True)
    for point in samples():
        stream.append(point, received_at=point.timestamp)
        stream.drain(as_of=point.timestamp)
    assert len(stream.window(count=30).samples) == 30
    assert stream.window(count=3).samples == samples()[-3:]


def test_empty_drain_advances_watermark_and_prevents_late_arrival():
    stream = collector(max_lateness_s=0)
    assert stream.drain(as_of=START) == ()
    assert stream.state(as_of=START).watermark_at == START
    with pytest.raises(ValueError, match="watermark"):
        stream.append(samples()[0], received_at=START + timedelta(seconds=1))
    with pytest.raises(ValueError, match="watermark moved backwards"):
        stream.drain(as_of=START - timedelta(seconds=1))
    stream.append(samples()[1], received_at=START + timedelta(seconds=1))
    assert stream.drain(as_of=START + timedelta(seconds=1)) == (samples()[1],)
