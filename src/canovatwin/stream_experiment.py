"""Deterministic transport replay over the dynamic plant, separate from agent inputs."""

import json
from datetime import datetime, timedelta
from hashlib import sha256
from random import Random
from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from .contracts import Contract, SensorSample, TelemetryWindow
from .operating import GenerationMetadata, generate_operating_case
from .stream import RejectionReason, StreamCollector, StreamConfig, StreamRejection, StreamState

Delivery = Literal["ordered", "jitter", "outage"]


class StreamRecipe(Contract):
    replay_version: Literal["transport-1.0"] = "transport-1.0"
    generation: GenerationMetadata
    delivery: Delivery = "ordered"


class DeliveryEvent(Contract):
    sequence: int = Field(ge=1)
    at: AwareDatetime
    measurement_at: AwareDatetime | None = None
    sample_id: str | None = None
    outcome: Literal["accepted", "rejected", "dropped", "disconnect", "reconnect", "flush"]
    reason: RejectionReason | None = None
    state: StreamState


class StreamExperiment(Contract):
    recipe: StreamRecipe
    config: StreamConfig
    as_of: AwareDatetime
    generated: int = Field(ge=3, le=600)
    accepted: int = Field(ge=3, le=600)
    rejected: int = Field(ge=0)
    dropped: int = Field(ge=0, le=600)
    events: tuple[DeliveryEvent, ...] = Field(min_length=1, max_length=650)
    final_state: StreamState
    window: TelemetryWindow
    trace_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def coherent_trace(self):
        if (
            self.window.source != "synthetic"
            or self.config.asset_id != self.window.asset_id
            or self.recipe.generation.asset_id != self.window.asset_id
        ):
            raise ValueError("Transport replay requires its own synthetic asset window")
        for outcome in ("accepted", "rejected", "dropped"):
            if sum(event.outcome == outcome for event in self.events) != getattr(self, outcome):
                raise ValueError("Transport counters disagree with the event trace")
        if self.accepted != len(self.window.samples):
            raise ValueError("Accepted count disagrees with the analysis window")
        accepted = {(e.sample_id, e.measurement_at) for e in self.events if e.outcome == "accepted"}
        if accepted != {(s.sample_id, s.timestamp) for s in self.window.samples}:
            raise ValueError("Accepted event identity disagrees with the analysis window")
        previous = self.events[0].at
        for sequence, event in enumerate(self.events, start=1):
            if event.sequence != sequence or event.at < previous:
                raise ValueError("Transport events are not sequential")
            previous = event.at
        if self.events[-1].outcome != "flush" or self.events[-1].at != self.as_of:
            raise ValueError("Transport trace must end at its observation clock")
        if self.final_state != self.events[-1].state or self.final_state.pending:
            raise ValueError("Final transport state disagrees with its trace")
        if self.trace_sha256 != _fingerprint(self.recipe, self.events, self.window):
            raise ValueError("Transport trace fingerprint does not match")
        return self


def _fingerprint(recipe: StreamRecipe, events, window: TelemetryWindow) -> str:
    # transport-1.0 predates asset selection. Preserve its default-asset hash.
    recipe_data = recipe.model_dump(mode="json")
    if recipe.generation.asset_id == "synthetic-unit-01":
        recipe_data["generation"].pop("asset_id")
    return sha256(
        json.dumps(
            {
                "recipe": recipe_data,
                "events": [event.model_dump(mode="json") for event in events],
                "window": window.model_dump(mode="json"),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def run_stream_experiment(recipe: StreamRecipe) -> StreamExperiment:
    recipe = StreamRecipe.model_validate(recipe.model_dump())
    case = generate_operating_case(recipe.generation)
    config = StreamConfig(asset_id=case.window.asset_id, stale_after_s=10)
    collector = StreamCollector(config)
    rng = Random(recipe.generation.seed ^ 0x535452)
    start = recipe.generation.start
    outage_start = start + timedelta(seconds=recipe.generation.count // 3)
    outage_end = start + timedelta(seconds=recipe.generation.count // 2)
    scheduled: list[tuple[datetime, int, int, str, SensorSample | None]] = []
    if recipe.delivery == "outage":
        scheduled.extend(((outage_start, 0, -1, "disconnect", None), (outage_end, 0, -1, "reconnect", None)))
    for index, sample in enumerate(case.window.samples):
        if recipe.delivery == "outage" and outage_start <= sample.timestamp < outage_end:
            scheduled.append((sample.timestamp, 1, index, "dropped", sample))
            continue
        latency = round(rng.uniform(0.1, 6), 3) if recipe.delivery == "jitter" else 0.2
        arrival = sample.timestamp + timedelta(seconds=latency)
        scheduled.append((arrival, 2, index, "sample", sample))
        if recipe.delivery == "jitter" and index % 17 == 0:
            scheduled.append((arrival + timedelta(seconds=0.05), 3, index, "sample", sample))
    events = []
    accepted = rejected = dropped = 0

    def observe(at, outcome, sample=None, reason=None):
        events.append(
            DeliveryEvent(
                sequence=len(events) + 1,
                at=at,
                measurement_at=None if sample is None else sample.timestamp,
                sample_id=None if sample is None else sample.sample_id,
                outcome=outcome,
                reason=reason,
                state=collector.state(as_of=at),
            )
        )

    for at, _, _, kind, sample in sorted(scheduled, key=lambda item: item[:3]):
        if kind == "disconnect":
            collector.disconnect(at=at)
            observe(at, "disconnect")
        elif kind == "reconnect":
            collector.reconnect(at=at)
            observe(at, "reconnect")
        elif kind == "dropped":
            # Only a simulated transport can know a packet was dropped at the source.
            dropped += 1
            collector.drain(as_of=at)
            observe(at, "dropped", sample)
        else:
            try:
                collector.append(sample, received_at=at)
                accepted += 1
                outcome, reason = "accepted", None
            except StreamRejection as exc:
                rejected += 1
                outcome, reason = "rejected", exc.reason
            collector.drain(as_of=at)
            observe(at, outcome, sample, reason)
    as_of = max(case.observation_time, max(item[0] for item in scheduled)) + timedelta(seconds=8)
    collector.drain(as_of=as_of)
    observe(as_of, "flush")
    if accepted < 3:
        raise ValueError("Fewer than three measurements survived the transport replay")
    window = collector.window(count=accepted)
    return StreamExperiment(
        recipe=recipe,
        config=config,
        as_of=as_of,
        generated=len(case.window.samples),
        accepted=accepted,
        rejected=rejected,
        dropped=dropped,
        events=tuple(events),
        final_state=collector.state(as_of=as_of),
        window=window,
        trace_sha256=_fingerprint(recipe, events, window),
    )
