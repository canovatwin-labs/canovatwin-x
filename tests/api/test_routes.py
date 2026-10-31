import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from canovatwin.api.app import create_app
from canovatwin.persistence.sqlite import SQLiteRepository
from canovatwin.telemetry import Scenario


@pytest.mark.parametrize("scenario", list(Scenario))
def test_all_scenarios_are_persisted(api, writer, scenario):
    response = api.post(
        "/api/v1/analyses/scenario",
        headers=writer,
        json={"scenario": scenario.value, "start": "2026-10-28T00:00:00Z"},
    )
    assert response.status_code == 201, response.text
    record = response.json()
    assert record["actor"] == "api-writer"
    assert record["engine_version"] == "0.4.0"
    assert record["result"]["status"] == "completed"
    assert record["result"]["commands"] == [] and record["result"]["llm_calls"] == 0
    assert record["result"]["report"]["research"] is not None
    loaded = api.get("/api/v1/runs/" + record["run_id"], headers=writer)
    assert loaded.status_code == 200 and loaded.json() == record


@pytest.mark.parametrize("profile", ["core6", "mvp12"])
def test_core_and_extended_profiles(api, writer, profile):
    response = api.post(
        "/api/v1/analyses/scenario", headers=writer, json={"scenario": "fan_loss", "profile": profile}
    )
    assert response.status_code == 201
    trace = response.json()["result"]["trace"]
    assert len(trace) == (6 if profile == "core6" else 10)


def test_strict_core_contract_accepts_json_dates_and_arrays(api, writer, request_factory):
    body = json.loads(request_factory(Scenario.FAN_LOSS).model_dump_json())
    response = api.post("/api/v1/analyses", headers=writer, json={"request": body})
    assert response.status_code == 201, response.text
    assert response.json()["request"] == body
    assert len(response.json()["result"]["trace"]) == 6


def test_controlled_block_is_business_result_not_server_failure(api, writer, request_factory):
    response = api.post(
        "/api/v1/analyses",
        headers=writer,
        json={"request": json.loads(request_factory().model_dump_json()), "policy": {"max_agents": 1}},
    )
    assert response.status_code == 201
    result = response.json()["result"]
    assert result["status"] == "blocked" and result["report"] is None
    assert result["failure"]["code"] == "AGENT_BUDGET_EXCEEDED"


def test_complete_lifecycle_and_replay(api, writer, reader):
    record = api.post("/api/v1/analyses/scenario", headers=writer, json={"scenario": "cooling_loss"}).json()
    incident_id = record["result"]["incident_id"]
    base = "/api/v1/incidents/" + incident_id
    assert api.get("/api/v1/incidents", headers=reader).json()["items"][0]["incident_id"] == incident_id
    assert api.get(base, headers=reader).json()["revision"] == 1
    assert api.get(base + "/runs", headers=reader).json()["items"][0]["run_id"] == record["run_id"]
    for revision, target in [(1, "investigating"), (2, "closed")]:
        response = api.post(
            base + "/status",
            headers=writer,
            json={"target": target, "expected_revision": revision, "reason": "İnceleme kararı"},
        )
        assert response.status_code == 200 and response.json()["revision"] == revision + 1
    replay = api.post("/api/v1/runs/" + record["run_id"] + "/replay", headers=writer)
    assert replay.status_code == 201 and replay.json()["matches"]
    assert replay.json()["record"]["replay_of"] == record["run_id"]
    after = api.get(base, headers=reader).json()
    assert after["status"] == "closed" and after["run_count"] == 2 and after["revision"] == 4
    audit = api.get(base + "/audit", headers=reader).json()["items"]
    assert len(audit) == 5
    assert all(event["actor"] == "api-writer" for event in audit)
    assert api.get("/api/v1/runs/" + record["run_id"], headers=reader).json() == record


def test_replay_preserves_captured_history(api, writer):
    past = api.post(
        "/api/v1/analyses/scenario",
        headers=writer,
        json={"scenario": "fan_loss", "start": "2026-10-27T00:00:00Z"},
    ).json()
    current = api.post(
        "/api/v1/analyses/scenario",
        headers=writer,
        json={"scenario": "fan_loss", "start": "2026-10-28T00:00:00Z"},
    ).json()
    assert len(current["result"]["trace"]) == 11
    assert current["request"]["research"]["historical_cases"][0]["run_id"] == past["run_id"]
    replay = api.post("/api/v1/runs/" + current["run_id"] + "/replay", headers=writer, json={}).json()
    assert replay["matches"] and replay["record"]["request"] == current["request"]


def test_explicit_request_is_never_augmented_from_live_history(api, writer, request_factory):
    api.post(
        "/api/v1/analyses/scenario",
        headers=writer,
        json={"scenario": "fan_loss", "start": "2026-10-27T00:00:00Z"},
    )
    request = json.loads(request_factory(Scenario.FAN_LOSS).model_dump_json())
    request["research"] = {"documents": [], "historical_cases": []}
    response = api.post("/api/v1/analyses", headers=writer, json={"request": request})
    assert response.status_code == 201
    assert response.json()["request"]["research"]["historical_cases"] == []
    assert len(response.json()["result"]["trace"]) == 9


def test_registry_health_and_pagination(api, reader, writer):
    assert api.get("/health").status_code == 200
    ready = api.get("/api/v1/health", headers=reader).json()
    assert ready["application_version"] == "0.16.0" and ready["engine_version"] == "0.4.0"
    assert ready["registered_agents"] == 36 and ready["active_agents"] == 12
    catalog = api.get("/api/v1/agents", headers=reader).json()
    assert len(catalog) == 36 and sum(a["status"] == "active" for a in catalog) == 12
    assert api.get("/api/v1/incidents", headers=reader).json()["items"] == []
    for scenario in ("fan_loss", "cooling_loss"):
        assert (
            api.post("/api/v1/analyses/scenario", headers=writer, json={"scenario": scenario}).status_code
            == 201
        )
    first = api.get("/api/v1/incidents?limit=1", headers=reader).json()
    second = api.get("/api/v1/incidents?limit=1&offset=1", headers=reader).json()
    assert first["limit"] == 1 and second["offset"] == 1
    assert first["items"][0]["incident_id"] != second["items"][0]["incident_id"]
    assert api.get("/api/v1/incidents?status=closed", headers=reader).json()["items"] == []


def test_history_survives_application_restart(api_settings, writer, reader):
    with TestClient(create_app(api_settings)) as client:
        record = client.post("/api/v1/analyses/scenario", headers=writer, json={}).json()
    with TestClient(create_app(api_settings)) as client:
        assert client.get("/api/v1/runs/" + record["run_id"], headers=reader).json() == record


def test_concurrent_writes_use_separate_sqlite_connections(api, writer, api_settings):
    def analyze(index):
        return api.post(
            "/api/v1/analyses/scenario",
            headers=writer,
            json={"scenario": "fan_loss", "start": "2026-10-28T00:00:00Z", "capture_history": False},
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(analyze, range(8)))
    assert all(r.status_code == 201 for r in responses), [(r.status_code, r.text) for r in responses]
    records = [r.json() for r in responses]
    assert len({r["run_id"] for r in records}) == 8
    assert len({r["result"]["incident_id"] for r in records}) == 1
    with SQLiteRepository(api_settings.database, read_only=True) as repo:
        incident = repo.get_incident(records[0]["result"]["incident_id"])
        assert incident.run_count == incident.revision == 8
        assert len(repo.audit(incident.incident_id)) == 9


def test_legacy_archive_is_readable_but_not_replayed_as_new_engine(api, api_settings, writer, reader):
    from pathlib import Path

    from canovatwin.persistence.models import RecordedAnalysis

    raw = (Path(__file__).resolve().parents[1] / "fixtures/legacy_v03_record.json").read_bytes()
    record = RecordedAnalysis.model_validate_json(raw)
    with SQLiteRepository(api_settings.database) as repo:
        repo.save(record)
    response = api.get("/api/v1/runs/" + record.run_id, headers=reader)
    assert response.status_code == 200 and response.json()["engine_version"] == "0.3.0"
    replay = api.post("/api/v1/runs/" + record.run_id + "/replay", headers=writer)
    assert replay.status_code == 409 and replay.json()["error"]["code"] == "REPLAY_INCOMPATIBLE"
    with SQLiteRepository(api_settings.database, read_only=True) as repo:
        assert repo.get_incident(record.result.incident_id).run_count == 1


def test_partial_policy_preserves_extended_profile_budgets(api, writer, request_factory):
    request = json.loads(request_factory(Scenario.FAN_LOSS).model_dump_json())
    request["research"] = {"documents": []}
    response = api.post(
        "/api/v1/analyses", headers=writer, json={"request": request, "policy": {"max_age_s": 45.0}}
    )
    assert response.status_code == 201
    record = response.json()
    assert record["result"]["status"] == "completed"
    assert record["policy"]["max_agents"] == record["policy"]["max_tool_calls"] == 12
    assert record["policy"]["max_age_s"] == 45.0
