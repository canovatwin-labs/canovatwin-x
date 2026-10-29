import json
import stat
import sys

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from canovatwin.api.app import create_app
from canovatwin.api.server import main
from canovatwin.api.settings import APISettings, initialize_config, load_settings


def test_initializer_creates_private_keys_without_overwriting(tmp_path, capsys, monkeypatch):
    path = tmp_path / "local" / "api.json"
    monkeypatch.setattr(sys, "argv", ["canovatwin-api", "init", "--config", str(path)])
    assert main() == 0
    out = capsys.readouterr()
    raw = json.loads(path.read_text())
    assert raw["read_token"] != raw["write_token"]
    assert len(raw["read_token"]) >= 32
    assert raw["read_token"] not in out.out + out.err and raw["write_token"] not in out.out + out.err
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    original = path.read_bytes()
    assert main() == 2
    assert path.read_bytes() == original
    loaded = load_settings(path)
    assert loaded.database == path.parent.resolve() / "history.sqlite3"
    assert raw["write_token"] not in repr(loaded)


@pytest.mark.parametrize(
    "change",
    [
        {"read_token": "short"},
        {"read_token": "a" * 31 + "ş"},
        {"read_token": "a " * 32},
        {"port": 0},
        {"max_request_bytes": 3_000_000},
        {"allowed_origins": ("*",)},
        {"allowed_origins": ("http://localhost:5173/path",)},
        {"allowed_origins": ("http://user:pass@localhost",)},
        {"allowed_origins": ("http://localhost:bad",)},
    ],
)
def test_bad_settings_are_rejected(api_settings, change):
    if "read_token" in change:
        change["read_token"] = SecretStr(change["read_token"])
    with pytest.raises(ValidationError):
        APISettings.model_validate(api_settings.model_dump() | change)


def test_reader_and_writer_must_use_different_keys(api_settings):
    with pytest.raises(ValidationError):
        APISettings.model_validate(api_settings.model_dump() | {"write_token": api_settings.read_token})


def test_origin_duplicates_are_removed(api_settings):
    settings = APISettings.model_validate(
        api_settings.model_dump() | {"allowed_origins": ("http://localhost:5173", "http://localhost:5173")}
    )
    assert settings.allowed_origins == ("http://localhost:5173",)


def test_bad_configuration_does_not_leak_secrets(tmp_path, monkeypatch, capsys):
    path = tmp_path / "api.json"
    path.write_text(
        json.dumps({"database": "x", "read_token": "private-secret", "write_token": "private-secret"})
    )
    monkeypatch.setattr(sys, "argv", ["canovatwin-api", "--config", str(path)])
    assert main() == 2
    output = capsys.readouterr()
    assert "private-secret" not in output.err


def test_large_configuration_is_rejected(tmp_path):
    path = tmp_path / "api.json"
    path.write_text(" " * 16001)
    with pytest.raises(ValueError):
        load_settings(path)


def test_server_binds_loopback_with_no_access_log(tmp_path, monkeypatch):
    path = tmp_path / "api.json"
    initialize_config(path)
    import canovatwin.api.server as module

    called = {}

    def run(app, **kwargs):
        called.update(kwargs)

    monkeypatch.setattr(module.uvicorn, "run", run)
    monkeypatch.setattr(sys, "argv", ["canovatwin-api", "--config", str(path)])
    assert main() == 0
    assert called == {"host": "127.0.0.1", "port": 8000, "access_log": False}


def test_openapi_contains_resolvable_strict_request_contracts(api, api_settings):
    response = api.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["version"] == "0.7.0"
    definitions = schema["components"]["schemas"]
    for name in ("AnalyzeBody", "ScenarioBody", "StatusBody", "ReplayBody"):
        assert definitions[name]["additionalProperties"] is False
        assert "actor" not in definitions[name].get("properties", {})
    operation = schema["paths"]["/api/v1/analyses"]["post"]
    assert (
        operation["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/AnalyzeBody"
    )
    assert operation["security"] == [{"LocalBearer": []}]

    def resolve(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "$ref":
                    assert item.startswith("#/"), item
                    current = schema
                    for segment in item[2:].split("/"):
                        current = current[segment.replace("~1", "/").replace("~0", "~")]
                else:
                    resolve(item)
        elif isinstance(value, list):
            for item in value:
                resolve(item)

    resolve(schema)
    assert api_settings.read_token.get_secret_value() not in response.text
    assert api_settings.write_token.get_secret_value() not in response.text


def test_cors_is_explicit_and_disabled_by_default(api, api_settings, reader):
    assert (
        "access-control-allow-origin"
        not in api.get("/health", headers={"Origin": "http://localhost:5173"}).headers
    )
    settings = api_settings.model_copy(update={"allowed_origins": ("http://localhost:5173",)})
    with TestClient(create_app(settings)) as client:
        response = client.options(
            "/api/v1/analyses",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
        assert "access-control-allow-credentials" not in response.headers
        denied = client.options(
            "/api/v1/analyses",
            headers={"Origin": "http://untrusted.example", "Access-Control-Request-Method": "POST"},
        )
        assert denied.status_code == 400
        assert "access-control-allow-origin" not in denied.headers
        unauthorized = client.get("/api/v1/incidents", headers={"Origin": "http://localhost:5173"})
        assert unauthorized.status_code == 401
        assert unauthorized.headers["access-control-allow-origin"] == "http://localhost:5173"


@pytest.mark.parametrize("origin", ["http://localhost:5173\n", "http://local host:5173"])
def test_origin_header_injection_is_rejected(api_settings, origin):
    with pytest.raises(ValidationError):
        APISettings.model_validate(api_settings.model_dump() | {"allowed_origins": (origin,)})


def test_browser_can_read_early_and_unexpected_errors(api_settings, writer, monkeypatch):
    from canovatwin.history import HistoryService

    settings = api_settings.model_copy(
        update={"allowed_origins": ("http://localhost:5173",), "max_request_bytes": 1024}
    )
    with TestClient(create_app(settings), raise_server_exceptions=False) as client:
        headers = {**writer, "Origin": "http://localhost:5173"}
        too_large = client.post("/api/v1/analyses/scenario", headers=headers, content="x" * 1025)
        assert too_large.status_code == 413
        assert too_large.headers["access-control-allow-origin"] == "http://localhost:5173"

        def crash(*args, **kwargs):
            raise RuntimeError("secret")

        monkeypatch.setattr(HistoryService, "analyze", crash)
        failed = client.post("/api/v1/analyses/scenario", headers=headers, json={})
        assert failed.status_code == 500
        assert failed.headers["access-control-allow-origin"] == "http://localhost:5173"
        assert "secret" not in failed.text
