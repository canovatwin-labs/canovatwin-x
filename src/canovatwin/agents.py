"""Twelve registered specialists share the same bounded, deterministic runtime."""

from types import MappingProxyType
from typing import Protocol

from .contracts import AgentPayload
from .runtime import ToolSession


class Specialist(Protocol):
    def execute(self, tools: ToolSession) -> AgentPayload: ...


class SensorValidator:
    def execute(self, tools: ToolSession) -> AgentPayload:
        return tools.call("check_sensor_quality")


class SignalAnalyzer:
    def execute(self, tools: ToolSession) -> AgentPayload:
        return tools.call("calculate_statistics")


class AnomalyInvestigator:
    def execute(self, tools: ToolSession) -> AgentPayload:
        return tools.call("detect_anomalies")


class RootCauseAnalyst:
    def execute(self, tools: ToolSession) -> AgentPayload:
        return tools.call("evaluate_causes")


class EvidenceVerifier:
    def execute(self, tools: ToolSession) -> AgentPayload:
        return tools.call("verify_evidence")


class ReportComposer:
    def execute(self, tools: ToolSession) -> AgentPayload:
        return tools.call("generate_report")


class MissingDataAnalyst:
    def execute(self, tools: ToolSession) -> AgentPayload:
        return tools.call("analyze_missing_data")


class HistoricalCaseMatcher:
    def execute(self, tools: ToolSession) -> AgentPayload:
        return tools.call("match_history")


class HypothesisCritic:
    def execute(self, tools: ToolSession) -> AgentPayload:
        return tools.call("critique_hypotheses")


class SimulationDesigner:
    def execute(self, tools: ToolSession) -> AgentPayload:
        return tools.call("design_simulation")


class SimulationValidator:
    def execute(self, tools: ToolSession) -> AgentPayload:
        return tools.call("validate_simulation")


class TechnicalDocumentRetriever:
    def execute(self, tools: ToolSession) -> AgentPayload:
        return tools.call("retrieve_documents")


_FACTORIES = MappingProxyType(
    {
        "A02": SensorValidator,
        "A03": SignalAnalyzer,
        "B02": AnomalyInvestigator,
        "B03": RootCauseAnalyst,
        "F03": EvidenceVerifier,
        "F04": ReportComposer,
        "A06": MissingDataAnalyst,
        "B05": HistoricalCaseMatcher,
        "B06": HypothesisCritic,
        "D02": SimulationDesigner,
        "D06": SimulationValidator,
        "F02": TechnicalDocumentRetriever,
    }
)


def build_specialist(agent_id: str) -> Specialist:
    try:
        return _FACTORIES[agent_id]()
    except KeyError:
        raise ValueError(f"Specialist {agent_id} is not implemented") from None
