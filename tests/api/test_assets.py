import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from canovatwin.api.app import create_app
from canovatwin.api.settings import APISettings
from canovatwin.assets import DEFAULT_ASSETS
from canovatwin.stream_experiment import StreamExperiment


def test_configured_catalog_is_read_only_and_empty_assets_are_visible(api, reader):
    assert api.get("/api/v1/assets").status_code == 401
    page = api.get("/api/v1/assets", headers=reader).json()
    assert [a["asset_id"] for a in page["items"]] == ["synthetic-unit-01", "synthetic-unit-02"]
    assert all(a["run_count"] == 0 and a["latest_run_id"] is None for a in page["items"])
    detail = api.get("/api/v1/assets/detail", headers=reader, params={"asset_id": "synthetic-unit-02"}).json()
    assert len(detail["channels"]) == 11
    assert next(c for c in detail["channels"] if c["field"] == "cooling_kw")["unit"] == "kW"
    assert "write_token" not in json.dumps(detail) and "read_token" not in json.dumps(detail)
    assert api.post("/api/v1/assets", headers=reader, json={}).status_code == 405


@pytest.mark.parametrize("dynamic", [False, True])
def test_asset_identity_scopes_generation_history_counts_filter_and_replay(api, reader, writer, dynamic):
    records = []
    for asset_id in ("synthetic-unit-01", "synthetic-unit-02"):
        body = {"asset_id": asset_id, "start": "2026-10-31T00:00:00Z", "capture_history": False}
        if dynamic:
            body["conditions"] = {"workload": "batch"}
        response = api.post("/api/v1/analyses/scenario", headers=writer, json=body)
        assert response.status_code == 201, response.text
        record = response.json()
        assert record["request"]["window"]["asset_id"] == asset_id
        if dynamic:
            assert record["generation"]["asset_id"] == asset_id
        records.append(record)
    assert records[0]["result"]["incident_id"] != records[1]["result"]["incident_id"]
    replay = api.post("/api/v1/runs/" + records[1]["run_id"] + "/replay", headers=writer).json()
    assert replay["matches"] is True
    assert replay["record"]["request"]["window"]["asset_id"] == "synthetic-unit-02"
    detail = api.get("/api/v1/assets/detail", headers=reader, params={"asset_id": "synthetic-unit-02"}).json()
    assert detail["asset"]["run_count"] == 2 and detail["asset"]["incident_count"] == 1
    assert detail["asset"]["latest_run_id"] == replay["record"]["run_id"]
    page = api.get("/api/v1/incidents", headers=reader, params={"asset_id": "synthetic-unit-01"}).json()
    assert len(page["items"]) == 1
    assert page["items"][0]["asset_id"] == "synthetic-unit-01"


def test_stream_recipe_and_collector_keep_selected_asset(api, reader, writer):
    response = api.post(
        "/api/v1/analyses/stream",
        headers=writer,
        json={"asset_id": "synthetic-unit-02", "delivery": "outage"},
    )
    assert response.status_code == 201, response.text
    record = response.json()
    report = record["stream_experiment"]
    assert report["recipe"]["generation"]["asset_id"] == report["window"]["asset_id"] == "synthetic-unit-02"
    replay = api.post("/api/v1/runs/" + record["run_id"] + "/replay", headers=writer).json()
    assert replay["matches"] is True and replay["record"]["stream_experiment"] == report


@pytest.mark.parametrize("path", ["scenario", "stream"])
def test_unknown_synthetic_target_is_rejected_without_history(api, writer, path):
    assert (
        api.post("/api/v1/analyses/" + path, headers=writer, json={"asset_id": "unknown"}).status_code == 422
    )
    assert api.get("/api/v1/incidents", headers=writer).json()["items"] == []


def test_legacy_observed_asset_and_sql_characters_are_not_lost_or_interpreted(api, reader, writer):
    initial = api.post("/api/v1/analyses/scenario", headers=writer, json={}).json()
    request = initial["request"]
    identifier = "Ölçüm/ünite?x=' OR 1=1--"
    request["window"]["asset_id"] = identifier
    assert api.post("/api/v1/analyses", headers=writer, json={"request": request}).status_code == 201
    detail = api.get("/api/v1/assets/detail", headers=reader, params={"asset_id": identifier})
    assert detail.status_code == 200
    assert detail.json()["asset"]["definition"] is None
    configured = api.get("/api/v1/assets", headers=reader, params={"configured_only": True}).json()
    assert len(configured["items"]) == 2
    page = api.get("/api/v1/incidents", headers=reader, params={"asset_id": identifier}).json()
    assert len(page["items"]) == 1 and page["items"][0]["asset_id"] == identifier
    assert (
        api.get("/api/v1/assets/detail", headers=reader, params={"asset_id": "' OR 1=1--"}).status_code == 404
    )


def test_config_rejects_duplicate_or_missing_default_asset(api_settings):
    for assets in ((DEFAULT_ASSETS[0], DEFAULT_ASSETS[0]), (DEFAULT_ASSETS[1],)):
        with pytest.raises(ValidationError, match="unique"):
            APISettings.model_validate(api_settings.model_dump() | {"assets": assets})


def test_pre_catalog_stream_fingerprint_remains_loadable(api, writer):
    record = api.post("/api/v1/analyses/stream", headers=writer, json={}).json()
    report = record["stream_experiment"]
    del report["recipe"]["generation"]["asset_id"]
    restored = StreamExperiment.model_validate_json(json.dumps(report))
    assert restored.trace_sha256 == report["trace_sha256"]


def test_retired_configuration_keeps_history_visible_after_restart(api, api_settings, reader, writer):
    record = api.post(
        "/api/v1/analyses/scenario", headers=writer, json={"asset_id": "synthetic-unit-02"}
    ).json()
    changed = api_settings.model_copy(update={"assets": (DEFAULT_ASSETS[0],)})
    with TestClient(create_app(changed)) as restarted:
        detail = restarted.get(
            "/api/v1/assets/detail", headers=reader, params={"asset_id": "synthetic-unit-02"}
        ).json()
        assert detail["asset"]["definition"] is None
        assert detail["asset"]["latest_run_id"] == record["run_id"]
        assert (
            restarted.post(
                "/api/v1/analyses/scenario", headers=writer, json={"asset_id": "synthetic-unit-02"}
            ).status_code
            == 422
        )


def test_catalog_pagination_and_per_asset_operating_defaults(api, writer):
    pages = [
        api.get("/api/v1/assets", headers=writer, params={"limit": 1, "offset": offset}).json()["items"]
        for offset in (0, 1, 2)
    ]
    assert [len(page) for page in pages] == [1, 1, 0]
    record = api.post(
        "/api/v1/analyses/stream",
        headers=writer,
        json={"asset_id": "synthetic-unit-02", "conditions": {"ambient_c": 32}},
    ).json()
    conditions = record["stream_experiment"]["recipe"]["generation"]["conditions"]
    assert conditions["baseline_load_kw"] == 6 and conditions["workload"] == "batch"
    assert conditions["ambient_c"] == 32
