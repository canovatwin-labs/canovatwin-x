"""Application service joining deterministic analysis with immutable history."""

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from .contracts import AnalysisRequest, AnalysisRun
from .operating import GenerationMetadata
from .persistence.errors import ReplayIncompatible
from .persistence.models import RecordedAnalysis, ReplayOutcome
from .persistence.repository import AnalysisRepository
from .policy import Policy, default_policy
from .supervisor import Supervisor
from .version import ENGINE_VERSION


def compare_results(before: AnalysisRun, after: AnalysisRun) -> tuple[str, ...]:
    """Elapsed time is measured anew; every other output/trace field must agree."""
    excluded = {"trace": {"__all__": {"elapsed_ms"}}}
    left, right = before.model_dump(exclude=excluded), after.model_dump(exclude=excluded)
    return tuple(key for key in left if left[key] != right[key])


class HistoryService:
    def __init__(self, repository: AnalysisRepository, *, clock: Callable[[], datetime] | None = None):
        self.repository = repository
        self._clock = clock or (lambda: datetime.now(UTC))

    def analyze(
        self,
        request: AnalysisRequest,
        *,
        policy: Policy | None = None,
        actor: str = "local-user",
        replay_of: str | None = None,
        generation: GenerationMetadata | None = None,
    ) -> RecordedAnalysis:
        policy = policy or default_policy(request)
        result = Supervisor(policy).run(request)
        record = RecordedAnalysis(
            run_id=f"RUN-{uuid4().hex}",
            recorded_at=self._clock(),
            actor=actor,
            engine_version=ENGINE_VERSION,
            request=request,
            policy=policy,
            result=result,
            replay_of=replay_of,
            generation=generation,
        )
        return self.repository.save(record)

    def replay(self, run_id: str, *, actor: str = "local-user") -> ReplayOutcome:
        original = self.repository.get_run(run_id)
        if original.engine_version != ENGINE_VERSION:
            raise ReplayIncompatible("Replay requires the same engine version as the recorded analysis")
        record = self.analyze(
            original.request,
            policy=original.policy,
            actor=actor,
            replay_of=run_id,
            generation=original.generation,
        )
        differences = compare_results(original.result, record.result)
        return ReplayOutcome(record=record, matches=not differences, differences=differences)
