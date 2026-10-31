"""Versioned HTTP routes over the existing analysis and history services."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from hmac import compare_digest
from typing import Annotated

from fastapi import Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.exceptions import HTTPException

from ..contracts import AnalysisRequest, ResearchInputs
from ..history import HistoryService
from ..knowledge import demo_documents
from ..operating import GenerationMetadata, generate_operating_case
from ..persistence.errors import (
    Conflict,
    InvalidTransition,
    NotFound,
    ReplayIncompatible,
    StorageBusy,
    StorageError,
)
from ..persistence.models import (
    AuditEvent,
    IncidentStatus,
    IncidentSummary,
    RecordedAnalysis,
    ReplayOutcome,
    RunSummary,
    Transition,
)
from ..persistence.sqlite import SQLiteRepository
from ..policy import Policy, default_policy
from ..registry import ACTIVE_IDS, REGISTRY, AgentDefinition
from ..snapshots import capture_history
from ..stream_experiment import StreamRecipe, run_stream_experiment
from ..telemetry import Scenario, generate_case
from ..version import ENGINE_VERSION
from .boundary import APIProblem, RequestBoundaryMiddleware, decode_body, error_response, safe_issues
from .models import (
    APPLICATION_VERSION,
    AnalyzeBody,
    ErrorEnvelope,
    Health,
    Page,
    Principal,
    Readiness,
    ReplayBody,
    ResourceId,
    ScenarioBody,
    StatusBody,
    StreamBody,
)
from .panel import register_panel
from .settings import APISettings

Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]


def create_app(settings: APISettings) -> FastAPI:
    settings = APISettings.model_validate(settings.model_dump())

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        with SQLiteRepository(settings.database, create=True):
            pass
        yield

    # Own the public wording: Python 3.12 and 3.13+ use different HTTP reason
    # phrases for 413/422, which otherwise changes the generated panel contract.
    error_descriptions = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        413: "Content Too Large",
        415: "Unsupported Media Type",
        422: "Unprocessable Content",
        500: "Internal Server Error",
        503: "Service Unavailable",
    }
    error_models = {
        code: {"model": ErrorEnvelope, "description": description}
        for code, description in error_descriptions.items()
    }
    app = FastAPI(
        title="CanovaTwin X",
        version=APPLICATION_VERSION,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        responses=error_models,
    )
    app.state.settings = settings
    register_panel(app)
    if settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.allowed_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type"],
            expose_headers=["X-Request-ID"],
        )
    app.add_middleware(RequestBoundaryMiddleware, limit=settings.max_request_bytes)
    bearer = HTTPBearer(scheme_name="LocalBearer", auto_error=False)

    def principal(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> Principal:
        token = credentials.credentials if credentials else ""
        if token and token.isascii() and len(token) <= 256:
            if compare_digest(token, settings.write_token.get_secret_value()):
                return Principal(role="writer", actor="api-writer")
            if compare_digest(token, settings.read_token.get_secret_value()):
                return Principal(role="reader", actor="api-reader")
        raise APIProblem(
            401,
            "AUTHENTICATION_REQUIRED",
            "A valid bearer token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    def reader(user: Annotated[Principal, Depends(principal)]) -> Principal:
        return user

    def writer(user: Annotated[Principal, Depends(principal)]) -> Principal:
        if user.role != "writer":
            raise APIProblem(403, "WRITE_PERMISSION_REQUIRED", "This operation requires writer access")
        return user

    async def analysis_body(request: Request, user: Annotated[Principal, Depends(writer)]) -> AnalyzeBody:
        return await decode_body(request, AnalyzeBody)

    async def scenario_body(request: Request, user: Annotated[Principal, Depends(writer)]) -> ScenarioBody:
        return await decode_body(request, ScenarioBody)

    async def status_body(request: Request, user: Annotated[Principal, Depends(writer)]) -> StatusBody:
        return await decode_body(request, StatusBody)

    async def stream_body(request: Request, user: Annotated[Principal, Depends(writer)]) -> StreamBody:
        return await decode_body(request, StreamBody)

    async def replay_body(request: Request, user: Annotated[Principal, Depends(writer)]) -> ReplayBody:
        return await decode_body(request, ReplayBody, optional=True)

    @app.exception_handler(APIProblem)
    async def api_problem(request: Request, error: APIProblem):
        return error_response(
            request, error.status, error.code, error.message, issues=error.issues, headers=error.headers
        )

    @app.exception_handler(RequestValidationError)
    async def invalid_parameters(request: Request, error: RequestValidationError):
        return error_response(
            request,
            422,
            "INVALID_REQUEST",
            "Request parameters do not match the contract",
            issues=safe_issues(error.errors()),
        )

    @app.exception_handler(StorageError)
    async def storage_failure(request: Request, error: StorageError):
        status = (
            404
            if isinstance(error, NotFound)
            else 409
            if isinstance(error, (Conflict, InvalidTransition, ReplayIncompatible))
            else 503
        )
        headers = {"Retry-After": "1"} if isinstance(error, StorageBusy) else None
        return error_response(
            request, status, error.code, "History operation could not be completed", headers=headers
        )

    @app.exception_handler(HTTPException)
    async def http_failure(request: Request, error: HTTPException):
        return error_response(
            request,
            error.status_code,
            f"HTTP_{error.status_code}",
            "HTTP request could not be completed",
            headers=error.headers,
        )

    @app.exception_handler(Exception)
    async def unexpected_failure(request: Request, error: Exception):
        return error_response(request, 500, "INTERNAL_ERROR", "The operation failed unexpectedly")

    @app.get("/health", response_model=Health)
    def health():
        return Health()

    @app.get("/api/v1/health", response_model=Readiness)
    def readiness(user: Annotated[Principal, Depends(reader)]):
        with SQLiteRepository(settings.database, read_only=True) as repo:
            repo.list_incidents(limit=1)
        return Readiness(
            engine_version=ENGINE_VERSION, registered_agents=len(REGISTRY), active_agents=len(ACTIVE_IDS)
        )

    @app.get("/api/v1/session", response_model=Principal)
    def session(user: Annotated[Principal, Depends(reader)]):
        return user

    @app.get("/api/v1/agents", response_model=tuple[AgentDefinition, ...])
    def agents(user: Annotated[Principal, Depends(reader)]):
        return REGISTRY

    @app.get("/api/v1/incidents", response_model=Page[IncidentSummary])
    def incidents(
        user: Annotated[Principal, Depends(reader)],
        status: IncidentStatus | None = None,
        limit: Limit = 20,
        offset: Offset = 0,
    ):
        with SQLiteRepository(settings.database, read_only=True) as repo:
            items = repo.list_incidents(status=status, limit=limit, offset=offset)
        return Page[IncidentSummary](items=items, limit=limit, offset=offset)

    @app.get("/api/v1/incidents/{incident_id}", response_model=IncidentSummary)
    def incident(incident_id: ResourceId, user: Annotated[Principal, Depends(reader)]):
        with SQLiteRepository(settings.database, read_only=True) as repo:
            return repo.get_incident(incident_id)

    @app.get("/api/v1/incidents/{incident_id}/runs", response_model=Page[RunSummary])
    def incident_runs(
        incident_id: ResourceId,
        user: Annotated[Principal, Depends(reader)],
        limit: Limit = 20,
        offset: Offset = 0,
    ):
        with SQLiteRepository(settings.database, read_only=True) as repo:
            items = repo.list_runs(incident_id, limit=limit, offset=offset)
        return Page[RunSummary](items=items, limit=limit, offset=offset)

    @app.get("/api/v1/incidents/{incident_id}/audit", response_model=Page[AuditEvent])
    def audit(
        incident_id: ResourceId,
        user: Annotated[Principal, Depends(reader)],
        limit: Limit = 20,
        offset: Offset = 0,
    ):
        with SQLiteRepository(settings.database, read_only=True) as repo:
            items = repo.audit(incident_id, limit=limit, offset=offset)
        return Page[AuditEvent](items=items, limit=limit, offset=offset)

    @app.get("/api/v1/runs/{run_id}", response_model=RecordedAnalysis)
    def analysis_run(run_id: ResourceId, user: Annotated[Principal, Depends(reader)]):
        with SQLiteRepository(settings.database, read_only=True) as repo:
            return repo.get_run(run_id)

    @app.post(
        "/api/v1/analyses",
        response_model=RecordedAnalysis,
        status_code=201,
        openapi_extra=_body_schema("AnalyzeBody"),
    )
    def analyze(
        body: Annotated[AnalyzeBody, Depends(analysis_body)], user: Annotated[Principal, Depends(writer)]
    ):
        policy = None
        if body.policy is not None:
            # A small override must not silently replace mvp12's budgets with
            # the standalone Policy model's core6 defaults.
            policy = Policy.model_validate(
                default_policy(body.request).model_dump() | body.policy.model_dump(exclude_unset=True)
            )
        with SQLiteRepository(settings.database) as repo:
            return HistoryService(repo).analyze(body.request, policy=policy, actor=user.actor)

    @app.post(
        "/api/v1/analyses/scenario",
        response_model=RecordedAnalysis,
        status_code=201,
        openapi_extra=_body_schema("ScenarioBody"),
    )
    def analyze_scenario(
        body: Annotated[ScenarioBody, Depends(scenario_body)], user: Annotated[Principal, Depends(writer)]
    ):
        if body.profile == "core6" and body.documents is not None:
            raise APIProblem(422, "INVALID_REQUEST", "Documents require the mvp12 profile")
        generation = None
        start = body.start or datetime.now(UTC)
        if body.conditions is not None:
            generation = GenerationMetadata(
                scenario=Scenario(body.scenario),
                count=body.count,
                seed=body.seed,
                start=start,
                conditions=body.conditions,
            )
            case = generate_operating_case(generation)
        else:
            case = generate_case(Scenario(body.scenario), count=body.count, seed=body.seed, start=start)
        research = (
            ResearchInputs(documents=body.documents if body.documents is not None else demo_documents())
            if body.profile == "mvp12"
            else None
        )
        request = AnalysisRequest(window=case.window, as_of=case.observation_time, research=research)
        with SQLiteRepository(settings.database) as repo:
            if body.capture_history:
                request = capture_history(repo, request)
            return HistoryService(repo).analyze(request, actor=user.actor, generation=generation)

    @app.post(
        "/api/v1/analyses/stream",
        response_model=RecordedAnalysis,
        status_code=201,
        openapi_extra=_body_schema("StreamBody"),
    )
    def analyze_stream(
        body: Annotated[StreamBody, Depends(stream_body)], user: Annotated[Principal, Depends(writer)]
    ):
        recipe = StreamRecipe(
            generation=GenerationMetadata(
                scenario=body.scenario,
                count=body.count,
                seed=body.seed,
                start=body.start or datetime.now(UTC),
                conditions=body.conditions,
            ),
            delivery=body.delivery,
        )
        try:
            experiment = run_stream_experiment(recipe)
        except ValueError:
            raise APIProblem(
                422, "INVALID_REQUEST", "Transport replay has insufficient valid samples"
            ) from None
        research = ResearchInputs(documents=demo_documents()) if body.profile == "mvp12" else None
        request = AnalysisRequest(window=experiment.window, as_of=experiment.as_of, research=research)
        with SQLiteRepository(settings.database) as repo:
            return HistoryService(repo).analyze(request, actor=user.actor, stream_experiment=experiment)

    @app.post(
        "/api/v1/incidents/{incident_id}/status",
        response_model=IncidentSummary,
        openapi_extra=_body_schema("StatusBody"),
    )
    def change_status(
        incident_id: ResourceId,
        body: Annotated[StatusBody, Depends(status_body)],
        user: Annotated[Principal, Depends(writer)],
    ):
        change = Transition(
            incident_id=incident_id,
            target=body.target,
            expected_revision=body.expected_revision,
            reason=body.reason,
            actor=user.actor,
        )
        with SQLiteRepository(settings.database) as repo:
            return repo.transition(change)

    @app.post(
        "/api/v1/runs/{run_id}/replay",
        response_model=ReplayOutcome,
        status_code=201,
        openapi_extra=_body_schema("ReplayBody", required=False),
    )
    def replay(
        run_id: ResourceId,
        body: Annotated[ReplayBody, Depends(replay_body)],
        user: Annotated[Principal, Depends(writer)],
    ):
        with SQLiteRepository(settings.database) as repo:
            return HistoryService(repo).replay(run_id, actor=user.actor)

    # Core contracts are deliberately strict. Raw JSON decoding preserves their JSON
    # date/tuple semantics while the same schemas remain visible to OpenAPI clients.
    original_openapi = app.openapi

    def openapi():
        schema = original_openapi()
        definitions = schema.setdefault("components", {}).setdefault("schemas", {})
        for model in (AnalyzeBody, ScenarioBody, StatusBody, ReplayBody, StreamBody):
            generated = model.model_json_schema(ref_template="#/components/schemas/{model}")
            definitions.update(generated.pop("$defs", {}))
            definitions[model.__name__] = generated
        return schema

    app.openapi = openapi
    return app


def _body_schema(name: str, *, required: bool = True) -> dict:
    return {
        "requestBody": {
            "required": required,
            "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{name}"}}},
        }
    }
