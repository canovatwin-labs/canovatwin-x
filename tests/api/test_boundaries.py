import json
import sqlite3
from contextlib import closing

import pytest
from fastapi.testclient import TestClient

from canovatwin.api.app import create_app
from canovatwin.persistence.errors import StorageError
from canovatwin.persistence.sqlite import SQLiteRepository


@pytest.mark.parametrize(
    "path", ["/api/v1/health", "/api/v1/agents", "/api/v1/incidents", "/api/v1/runs/RUN-missing"]
)
@pytest.mark.parametrize("authorization", [None, "Bearer wrong", "Basic wrong", "Bearer"])
def test_missing_or_invalid_auth_is_rejected(api, path, authorization):
    response = api.get(path, headers={"Authorization": authorization} if authorization else {})
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.parametrize(
    ("path", "body"),
    [
        ("/api/v1/analyses/scenario", {}),
        ("/api/v1/analyses", {}),
        ("/api/v1/incidents/INC-missing/status", {"target": "closed", "expected_revision": 1, "reason": "x"}),
        ("/api/v1/runs/RUN-missing/replay", {}),
    ],
)
def test_reader_cannot_mutate_state(api, reader, api_settings, path, body):
    response = api.post(path, headers=reader, json=body)
    assert response.status_code == 403 and response.json()["error"]["code"] == "WRITE_PERMISSION_REQUIRED"
    with SQLiteRepository(api_settings.database, read_only=True) as repo:
        assert repo.list_incidents() == ()


@pytest.mark.parametrize(
    "change",
    [
        {"actor": "forged-user"},
        {"count": "120"},
        {"seed": True},
        {"count": 601},
        {"profile": "all36"},
        {"scenario": "unknown"},
        {"start": "2026-10-28"},
    ],
)
def test_bad_scenario_input_never_writes(api, writer, api_settings, change):
    response = api.post("/api/v1/analyses/scenario", headers=writer, json=change)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
    with SQLiteRepository(api_settings.database, read_only=True) as repo:
        assert repo.list_incidents() == ()


@pytest.mark.parametrize(
    ("field", "value"), [("inlet_c", "23"), ("inlet_c", True), ("inlet_c", float("nan"))]
)
def test_strict_telemetry_validation_over_http(api, writer, request_factory, field, value):
    request = json.loads(request_factory().model_dump_json())
    request["window"]["samples"][0][field] = value
    # Deliberately serialize NaN as hostile raw JSON; the boundary must reject it.
    response = api.post(
        "/api/v1/analyses",
        headers={**writer, "Content-Type": "application/json"},
        content=json.dumps({"request": request}),
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("content", "content_type", "status"),
    [
        ("private-invalid-json", "application/json", 422),
        ("{}", "text/plain", 415),
        ("[]", "application/json", 422),
        ("", "application/json", 422),
    ],
)
def test_invalid_body_errors_are_redacted(api, writer, content, content_type, status):
    response = api.post(
        "/api/v1/analyses/scenario", headers={**writer, "Content-Type": content_type}, content=content
    )
    assert response.status_code == status
    assert "private-invalid-json" not in response.text
    assert response.headers["X-Request-ID"] == response.json()["request_id"]
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/incidents/INC-unknown",
        "/api/v1/runs/RUN-unknown",
        "/api/v1/incidents/INC-unknown/runs",
        "/api/v1/incidents/INC-unknown/audit",
    ],
)
def test_missing_resources_are_404(api, reader, path):
    response = api.get(path, headers=reader)
    assert response.status_code == 404 and response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1", "status=wrong"])
def test_invalid_query_parameters(api, reader, query):
    response = api.get("/api/v1/incidents?" + query, headers=reader)
    assert response.status_code == 422 and response.json()["error"]["issues"]


def test_stale_revision_and_illegal_transition_are_conflicts(api, writer):
    record = api.post("/api/v1/analyses/scenario", headers=writer, json={}).json()
    base = "/api/v1/incidents/" + record["result"]["incident_id"]
    assert (
        api.post(
            base + "/status",
            headers=writer,
            json={"target": "closed", "expected_revision": 1, "reason": "Skip review"},
        ).status_code
        == 409
    )
    assert (
        api.post(
            base + "/status",
            headers=writer,
            json={"target": "investigating", "expected_revision": 1, "reason": "Start"},
        ).status_code
        == 200
    )
    conflict = api.post(
        base + "/status",
        headers=writer,
        json={"target": "investigating", "expected_revision": 1, "reason": "Stale"},
    )
    assert conflict.status_code == 409 and conflict.json()["error"]["code"] == "CONFLICT"
    assert len(api.get(base + "/audit", headers=writer).json()["items"]) == 3


def test_lifecycle_actor_cannot_be_spoofed(api, writer):
    record = api.post("/api/v1/analyses/scenario", headers=writer, json={}).json()
    path = "/api/v1/incidents/" + record["result"]["incident_id"] + "/status"
    response = api.post(
        path,
        headers=writer,
        json={"target": "investigating", "expected_revision": 1, "reason": "x", "actor": "CEO"},
    )
    assert response.status_code == 422


def test_body_limits_cover_declared_and_chunked_bodies(api_settings, writer):
    settings = api_settings.model_copy(update={"max_request_bytes": 1024})
    with TestClient(create_app(settings)) as client:
        response = client.post("/api/v1/analyses/scenario", headers=writer, content="x" * 1025)
        assert response.status_code == 413

        def chunks():
            yield b" " * 700
            yield b" " * 700

        response = client.post(
            "/api/v1/analyses/scenario",
            headers={**writer, "Content-Type": "application/json"},
            content=chunks(),
        )
        assert response.status_code == 413
        assert client.get("/api/v1/incidents", headers=writer).json()["items"] == []


@pytest.mark.parametrize("length", ["-1", "invalid", "999999999999999"])
def test_invalid_content_length_is_controlled(api, writer, length):
    response = api.post(
        "/api/v1/analyses/scenario", headers={**writer, "Content-Length": length}, content="{}"
    )
    assert response.status_code == 400


def test_foreign_schemas_fail_startup_without_overwriting_data(api_settings):
    with closing(sqlite3.connect(api_settings.database)) as db:
        db.execute("CREATE TABLE unrelated(value TEXT)")
        db.execute("INSERT INTO unrelated VALUES (?)", ("keep-me",))
        db.commit()
    with pytest.raises(StorageError), TestClient(create_app(api_settings)):
        pass
    with closing(sqlite3.connect(api_settings.database)) as db:
        assert db.execute("SELECT value FROM unrelated").fetchall() == [("keep-me",)]


def test_corruption_returns_service_error_without_payload_leak(api, writer, api_settings):
    record = api.post("/api/v1/analyses/scenario", headers=writer, json={}).json()
    with closing(sqlite3.connect(api_settings.database)) as db:
        db.execute("UPDATE analysis_runs SET payload=?", ("private-record-payload",))
        db.commit()
    response = api.get("/api/v1/runs/" + record["run_id"], headers=writer)
    assert response.status_code == 503 and response.json()["error"]["code"] == "CORRUPT_RECORD"
    assert "private-record-payload" not in response.text


def test_busy_database_returns_retryable_error(api, writer, api_settings):
    # Force the mapped StorageBusy condition without a five-second sleep.
    from unittest.mock import patch

    import canovatwin.api.app as module
    from canovatwin.persistence.errors import StorageBusy

    with patch.object(module, "SQLiteRepository", side_effect=StorageBusy("private-lock-message")):
        response = api.get("/api/v1/incidents", headers=writer)
    assert response.status_code == 503 and response.headers["Retry-After"] == "1"
    assert "private-lock-message" not in response.text


def test_unexpected_errors_are_redacted(api, writer, monkeypatch):
    from canovatwin.history import HistoryService

    def fail(*args, **kwargs):
        raise RuntimeError("private-company-secret")

    monkeypatch.setattr(HistoryService, "analyze", fail)
    response = api.post("/api/v1/analyses/scenario", headers=writer, json={})
    assert response.status_code == 500 and response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "private-company-secret" not in response.text
    assert response.headers["X-Request-ID"] == response.json()["request_id"]


def test_unknown_paths_and_methods_use_error_envelope(api):
    assert api.get("/not-a-route").json()["error"]["code"] == "HTTP_404"
    assert api.post("/health", json={}).json()["error"]["code"] == "HTTP_405"
