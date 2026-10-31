import pytest
from fastapi.testclient import TestClient

from canovatwin.api.app import create_app


@pytest.mark.parametrize("delivery", ["ordered", "jitter", "outage"])
def test_stream_experiment_is_saved_with_exact_window_and_replays(api, reader, writer, delivery):
    body = {"delivery": delivery, "start": "2026-10-31T00:00:00Z", "scenario": "fan_loss"}
    assert api.post("/api/v1/analyses/stream", headers=reader, json=body).status_code == 403
    response = api.post("/api/v1/analyses/stream", headers=writer, json=body)
    assert response.status_code == 201, response.text
    record = response.json()
    experiment = record["stream_experiment"]
    assert experiment["window"] == record["request"]["window"]
    assert experiment["as_of"] == record["request"]["as_of"]
    assert "stream_experiment" not in record["request"]
    assert "scenario" not in record["request"]
    assert record["result"]["llm_calls"] == 0 and record["result"]["commands"] == []
    assert api.get("/api/v1/runs/" + record["run_id"], headers=reader).json() == record
    replay = api.post("/api/v1/runs/" + record["run_id"] + "/replay", headers=writer).json()
    assert replay["matches"] is True
    assert replay["record"]["stream_experiment"] == experiment


@pytest.mark.parametrize("body", [{"delivery": "plc"}, {"count": 601}, {"seed": 2**60}, {"start": "bad"}])
def test_invalid_stream_body_does_not_create_history(api, writer, body):
    assert api.post("/api/v1/analyses/stream", headers=writer, json=body).status_code == 422
    assert api.get("/api/v1/incidents", headers=writer).json()["items"] == []


def test_stream_metadata_survives_application_restart(api, api_settings, reader, writer):
    record = api.post("/api/v1/analyses/stream", headers=writer, json={"delivery": "outage"}).json()
    with TestClient(create_app(api_settings)) as restarted:
        loaded = restarted.get("/api/v1/runs/" + record["run_id"], headers=reader)
        assert loaded.status_code == 200
        assert loaded.json() == record
