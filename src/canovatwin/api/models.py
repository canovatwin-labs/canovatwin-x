"""Wire contracts. Bodies are validated as JSON so strict core tuples/dates stay valid."""

from typing import Annotated, Literal

from pydantic import AwareDatetime, Field

from ..contracts import AnalysisRequest, Contract, Identifier, TechnicalDocument
from ..operating import OperatingConditions
from ..persistence.models import IncidentStatus, Reason
from ..policy import Policy

API_VERSION = "1.0"
APPLICATION_VERSION = "0.9.0"


class AnalyzeBody(Contract):
    request: AnalysisRequest
    policy: Policy | None = None


class ScenarioBody(Contract):
    scenario: Literal[
        "normal",
        "fan_loss",
        "sensor_bias",
        "sensor_missing",
        "load_surge",
        "cooling_loss",
        "airflow_restriction",
        "fan_mismatch",
        "communication_loss",
        "control_oscillation",
        "combined",
    ] = "normal"
    profile: Literal["core6", "mvp12"] = "mvp12"
    count: int = Field(default=120, ge=30, le=600)
    seed: int = 42
    start: AwareDatetime | None = None
    documents: tuple[TechnicalDocument, ...] | None = Field(default=None, max_length=8)
    capture_history: bool = True
    conditions: OperatingConditions | None = None


class StatusBody(Contract):
    target: IncidentStatus
    expected_revision: int = Field(ge=1)
    reason: Reason


class ReplayBody(Contract):
    pass


class Page[Item: Contract](Contract):
    items: tuple[Item, ...]
    limit: int
    offset: int


class Health(Contract):
    status: Literal["ok"] = "ok"
    mode: Literal["simulation"] = "simulation"
    api_version: str = API_VERSION
    application_version: str = APPLICATION_VERSION


class Readiness(Health):
    database: Literal["ready"] = "ready"
    engine_version: str
    registered_agents: int
    active_agents: int


class FieldIssue(Contract):
    location: tuple[str | int, ...]
    code: str
    message: str


class ErrorDetail(Contract):
    code: str
    message: str
    issues: tuple[FieldIssue, ...] = ()


class ErrorEnvelope(Contract):
    request_id: Identifier
    error: ErrorDetail


class Principal(Contract):
    role: Literal["reader", "writer"]
    actor: Literal["api-reader", "api-writer"]


ResourceId = Annotated[str, Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")]
