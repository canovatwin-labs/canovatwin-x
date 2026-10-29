"""Bounded JSON decoding and response-safe error mapping."""

from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.datastructures import MutableHeaders

from ..contracts import Contract
from .models import ErrorDetail, ErrorEnvelope, FieldIssue


class APIProblem(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        *,
        issues: tuple[FieldIssue, ...] = (),
        headers: dict[str, str] | None = None,
    ):
        self.status, self.code, self.message = status, code, message
        self.issues, self.headers = issues, headers or {}


def safe_issues(errors: list[dict]) -> tuple[FieldIssue, ...]:
    return tuple(
        FieldIssue(location=tuple(error["loc"]), code=error["type"], message=error["msg"])
        for error in errors[:20]
    )


def error_response(
    request: Request,
    status: int,
    code: str,
    message: str,
    *,
    issues: tuple[FieldIssue, ...] = (),
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", uuid4().hex)
    payload = ErrorEnvelope(
        request_id=request_id, error=ErrorDetail(code=code, message=message, issues=issues)
    )
    response_headers = {
        "X-Request-ID": request_id,
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        **(headers or {}),
    }
    # Early body rejections and outer 500 handlers can bypass CORSMiddleware.
    # Preserve the same explicit-origin policy for their JSON error responses.
    origin = request.headers.get("origin")
    settings = request.app.state.settings
    if origin in settings.allowed_origins:
        response_headers.update(
            {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Expose-Headers": "X-Request-ID",
                "Vary": "Origin",
            }
        )
    return JSONResponse(status_code=status, content=payload.model_dump(mode="json"), headers=response_headers)


async def decode_body[Model: Contract](
    request: Request, model: type[Model], *, optional: bool = False
) -> Model:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > request.app.state.settings.max_request_bytes:
            raise APIProblem(413, "PAYLOAD_TOO_LARGE", "Request body exceeds the configured limit")
        raw.extend(chunk)
    if not raw and optional:
        raw.extend(b"{}")
    elif content_type != "application/json":
        raise APIProblem(415, "UNSUPPORTED_MEDIA_TYPE", "Use application/json for request bodies")
    try:
        return model.model_validate_json(raw)
    except ValidationError as exc:
        raise APIProblem(
            422,
            "INVALID_REQUEST",
            "Request does not match its JSON contract",
            issues=safe_issues(exc.errors(include_input=False, include_context=False, include_url=False)),
        ) from None


class RequestBoundaryMiddleware:
    def __init__(self, app, *, limit: int):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request_id = uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id
        request = Request(scope)
        length = request.headers.get("content-length")
        if length is not None:
            if not length.isascii() or not length.isdigit() or len(length) > 12:
                response = error_response(request, 400, "INVALID_CONTENT_LENGTH", "Content-Length is invalid")
                await response(scope, receive, send)
                return
            if int(length) > self.limit:
                response = error_response(
                    request, 413, "PAYLOAD_TOO_LARGE", "Request body exceeds the configured limit"
                )
                await response(scope, receive, send)
                return

        async def with_headers(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
                headers["Cache-Control"] = "no-store"
                headers["X-Content-Type-Options"] = "nosniff"
            await send(message)

        await self.app(scope, receive, with_headers)
