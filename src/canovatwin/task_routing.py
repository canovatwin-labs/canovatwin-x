"""Versioned task metadata and per-analysis dispatch for the local supervisor."""

from collections.abc import Sequence
from typing import Literal

from .contracts import Contract, Identifier
from .registry import REGISTRY, AgentDefinition
from .runtime import Budget, ExecutionError
from .state import AnalysisContext

Capability = Literal[
    "quality",
    "signals",
    "anomaly",
    "diagnosis",
    "verification",
    "report",
    "missing_data",
    "history",
    "critique",
    "simulation",
    "simulation_validation",
    "retrieval",
]


class TaskEnvelope(Contract):
    schema_version: Literal["1.0"]
    incident_id: Identifier
    task_id: Identifier
    capability: Capability


class CapabilityRouter:
    def __init__(self, catalog: Sequence[AgentDefinition] = REGISTRY):
        self._routes: dict[str, AgentDefinition] = {}
        for agent in catalog:
            if agent.status != "active" or agent.execution != "deterministic":
                continue
            if agent.output_schema in self._routes:
                raise ExecutionError(
                    "AMBIGUOUS_CAPABILITY", "Multiple active specialists claim the capability"
                )
            self._routes[agent.output_schema] = agent

    def resolve(self, capability: Capability) -> AgentDefinition:
        definition = self._routes.get(capability)
        if definition is None:
            raise ExecutionError("CAPABILITY_UNAVAILABLE", "No active specialist implements the capability")
        return definition


def task_identifier(incident_id: str, definition: AgentDefinition) -> str:
    return f"TASK-{incident_id.removeprefix('INC-')}-{definition.agent_id}"


class LocalDispatcher:
    """Admit each task once per analysis, including tasks whose execution later fails."""

    def __init__(self, router: CapabilityRouter, ctx: AnalysisContext, budget: Budget):
        self._router = router
        self._incident_id = ctx.incident_id
        self._budget = budget
        self._admitted: set[str] = set()

    def admit(self, task: TaskEnvelope) -> AgentDefinition:
        task = TaskEnvelope.model_validate(task.model_dump())
        definition = self._router.resolve(task.capability)
        if task.incident_id != self._incident_id or task.task_id != task_identifier(
            self._incident_id, definition
        ):
            raise ExecutionError("TASK_SCOPE_MISMATCH", "Task does not match this incident and capability")
        if task.task_id in self._admitted:
            raise ExecutionError("DUPLICATE_TASK", "Task was already admitted in this analysis")
        self._budget.begin_agent()
        self._admitted.add(task.task_id)
        return definition
