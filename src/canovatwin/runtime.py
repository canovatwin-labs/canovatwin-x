"""Central tool authorization, budgets and cooperative deadline checks."""

from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic
from types import MappingProxyType

from .analysis.diagnosis import diagnose, investigate
from .analysis.evidence import verify
from .analysis.quality import check_quality
from .analysis.reporting import compose_report
from .analysis.research import analyze_missing_data, critique_hypotheses, match_history, retrieve_documents
from .analysis.signals import analyze_signals
from .analysis.simulation import design_simulation, validate_simulation
from .contracts import AgentPayload
from .policy import Policy
from .registry import AgentDefinition
from .state import AnalysisContext

TOOLS = MappingProxyType(
    {
        "check_sensor_quality": check_quality,
        "calculate_statistics": analyze_signals,
        "detect_anomalies": investigate,
        "evaluate_causes": diagnose,
        "verify_evidence": verify,
        "generate_report": compose_report,
        "analyze_missing_data": analyze_missing_data,
        "match_history": match_history,
        "retrieve_documents": retrieve_documents,
        "critique_hypotheses": critique_hypotheses,
        "design_simulation": design_simulation,
        "validate_simulation": validate_simulation,
    }
)


class ExecutionError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass
class Budget:
    policy: Policy
    clock: Callable[[], float] = monotonic
    started: float = 0.0
    tool_calls: int = 0
    agents: int = 0

    def __post_init__(self):
        self.started = self.clock()

    def check_deadline(self):
        if self.clock() - self.started >= self.policy.max_elapsed_s:
            raise ExecutionError("DEADLINE_EXCEEDED", "Analysis exceeded its elapsed-time budget")

    def begin_agent(self):
        self.check_deadline()
        if self.agents >= self.policy.max_agents:
            raise ExecutionError("AGENT_BUDGET_EXCEEDED", "Agent activation budget exhausted")
        self.agents += 1


class ToolSession:
    def __init__(self, definition: AgentDefinition, ctx: AnalysisContext, budget: Budget):
        self._definition = definition
        self._ctx = ctx
        self._budget = budget
        self.calls = 0

    def call(self, name: str) -> AgentPayload:
        if name not in self._definition.allowed_tools or name not in TOOLS:
            raise ExecutionError("TOOL_DENIED", "Tool is not permitted for this specialist")
        self._budget.check_deadline()
        if self.calls >= self._budget.policy.max_tools_per_agent:
            raise ExecutionError("AGENT_TOOL_BUDGET_EXCEEDED", "Specialist tool budget exhausted")
        if self._budget.tool_calls >= self._budget.policy.max_tool_calls:
            raise ExecutionError("TOOL_BUDGET_EXCEEDED", "Total tool budget exhausted")
        self.calls += 1
        self._budget.tool_calls += 1
        result = TOOLS[name](self._ctx)
        self._budget.check_deadline()
        return result
