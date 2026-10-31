"""Bounded event-time collector for offline telemetry replay.

This is a transport-independent contract. It does not connect to a PLC or
authorize control. Arrival time and measurement time remain separate.
"""

from bisect import insort
from datetime import datetime, timedelta
from typing import Literal

from pydantic import AwareDatetime, Field

from .contracts import Contract, SensorSample, TelemetryWindow

RejectionReason = Literal[
    "disconnected", "arrival_clock", "future", "late", "duplicate_id", "duplicate_timestamp", "buffer_full"
]


class StreamRejection(ValueError):
    def __init__(self, reason: RejectionReason, message: str):
        super().__init__(message)
        self.reason = reason


class StreamConfig(Contract):
    asset_id: str = Field(min_length=1, max_length=100)
    max_lateness_s: float = Field(default=2, ge=0, le=300)
    future_tolerance_s: float = Field(default=5, ge=0, le=60)
    stale_after_s: float = Field(default=60, gt=0, le=3600)
    max_pending: int = Field(default=600, ge=3, le=600)


class StreamState(Contract):
    connection: Literal["connected", "disconnected"]
    freshness: Literal["fresh", "stale", "empty"]
    pending: int
    committed: int
    last_measurement_at: AwareDatetime | None
    last_arrival_at: AwareDatetime | None
    watermark_at: AwareDatetime | None


class StreamCollector:
    """Sort a bounded lateness window and reject ambiguous or lost samples."""

    def __init__(self, config: StreamConfig):
        self.config = StreamConfig.model_validate(config.model_dump())
        self._pending: list[tuple[datetime, str, SensorSample]] = []
        self._recent: list[SensorSample] = []
        self._last_arrival: datetime | None = None
        self._last_committed: datetime | None = None
        self._watermark: datetime | None = None
        self._connected = True
        self._ids: set[str] = set()

    @staticmethod
    def _aware(value: datetime) -> None:
        if value.utcoffset() is None:
            raise ValueError("Clock timestamps must include a timezone")

    def append(self, sample: SensorSample, *, received_at: datetime) -> None:
        """Accept one measurement; backpressure and invalid clocks fail closed."""
        self._aware(received_at)
        sample = SensorSample.model_validate(sample.model_dump())
        if not self._connected:
            raise StreamRejection("disconnected", "Stream is disconnected")
        if self._last_arrival is not None and received_at < self._last_arrival:
            raise StreamRejection("arrival_clock", "Arrival clock moved backwards")
        if sample.timestamp > received_at + timedelta(seconds=self.config.future_tolerance_s):
            raise StreamRejection("future", "Measurement is in the future relative to arrival")
        if self._watermark is not None and sample.timestamp <= self._watermark:
            raise StreamRejection("late", "Measurement arrived after its event-time watermark")
        if sample.sample_id in self._ids:
            raise StreamRejection("duplicate_id", "Duplicate sample ID")
        if any(item[0] == sample.timestamp for item in self._pending):
            raise StreamRejection("duplicate_timestamp", "Duplicate measurement timestamp")
        if len(self._pending) >= self.config.max_pending:
            raise StreamRejection("buffer_full", "Pending buffer is full; caller must drain or retry")
        insort(self._pending, (sample.timestamp, sample.sample_id, sample))
        self._ids.add(sample.sample_id)
        self._last_arrival = received_at

    def drain(self, *, as_of: datetime) -> tuple[SensorSample, ...]:
        """Commit measurements older than the watermark in event-time order."""
        self._aware(as_of)
        if self._last_arrival is not None and as_of < self._last_arrival:
            raise ValueError("Watermark precedes the last arrival")
        cutoff = as_of - timedelta(seconds=self.config.max_lateness_s)
        if self._watermark is not None and cutoff < self._watermark:
            raise ValueError("Event-time watermark moved backwards")
        count = 0
        for timestamp, _, _ in self._pending:
            if timestamp > cutoff:
                break
            count += 1
        ready = tuple(item[2] for item in self._pending[:count])
        del self._pending[:count]
        self._watermark = cutoff
        if ready:
            self._last_committed = ready[-1].timestamp
            self._recent.extend(ready)
            self._recent = self._recent[-600:]
            self._ids = {sample.sample_id for sample in self._recent} | {
                sample.sample_id for _, _, sample in self._pending
            }
        return ready

    def disconnect(self, *, at: datetime) -> None:
        self._transition(at, connected=False)

    def reconnect(self, *, at: datetime) -> None:
        self._transition(at, connected=True)

    def _transition(self, at: datetime, *, connected: bool) -> None:
        self._aware(at)
        if self._last_arrival is not None and at < self._last_arrival:
            raise ValueError("Connection clock moved backwards")
        self._connected = connected
        self._last_arrival = at

    def state(self, *, as_of: datetime) -> StreamState:
        self._aware(as_of)
        if self._last_arrival is not None and as_of < self._last_arrival:
            raise ValueError("Observation clock moved backwards")
        latest = self._last_committed
        freshness: Literal["fresh", "stale", "empty"] = "empty"
        if latest is not None:
            freshness = "stale" if (as_of - latest).total_seconds() > self.config.stale_after_s else "fresh"
        if not self._connected:
            freshness = "stale" if latest is not None else "empty"
        return StreamState(
            connection="connected" if self._connected else "disconnected",
            freshness=freshness,
            pending=len(self._pending),
            committed=len(self._recent),
            last_measurement_at=latest,
            last_arrival_at=self._last_arrival,
            watermark_at=self._watermark,
        )

    def window(self, *, count: int) -> TelemetryWindow:
        if isinstance(count, bool) or not isinstance(count, int) or not 3 <= count <= 600:
            raise ValueError("Window count must be an integer between 3 and 600")
        if len(self._recent) < count:
            raise ValueError("Not enough committed measurements")
        return TelemetryWindow(asset_id=self.config.asset_id, samples=tuple(self._recent[-count:]))
