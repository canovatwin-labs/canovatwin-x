import pytest

from canovatwin.operating import GenerationMetadata, generate_operating_case
from canovatwin.telemetry import Scenario


@pytest.mark.parametrize("scenario", list(Scenario))
@pytest.mark.parametrize("workload", ["steady", "cyclic", "batch"])
def test_dynamic_scenarios_save_and_replay_without_ground_truth_leak(api, writer, scenario, workload):
    response = api.post(
        "/api/v1/analyses/scenario",
        headers=writer,
        json={
            "scenario": scenario.value,
            "count": 360,
            "start": "2026-10-28T00:00:00Z",
            "conditions": {"workload": workload},
        },
    )
    assert response.status_code == 201, response.text
    record = response.json()
    assert record["result"]["status"] == "completed"
    report = record["result"]["report"]
    if scenario == Scenario.NORMAL:
        assert report["status"] == "clear" and not report["hypotheses"]
    elif scenario in (Scenario.SENSOR_MISSING, Scenario.COMMUNICATION_LOSS):
        assert report["status"] == "insufficient_data"
    else:
        expected = {
            Scenario.FAN_LOSS: {"FAULT_F01"},
            Scenario.SENSOR_BIAS: {"FAULT_F02"},
            Scenario.LOAD_SURGE: {"FAULT_F04"},
            Scenario.COOLING_LOSS: {"FAULT_F05"},
            Scenario.AIRFLOW_RESTRICTION: {"FAULT_F06"},
            Scenario.FAN_MISMATCH: {"FAULT_F07"},
            Scenario.CONTROL_OSCILLATION: {"FAULT_F09"},
            Scenario.COMBINED: {"FAULT_F01", "FAULT_F05"},
        }[scenario]
        assert report["status"] == "needs_review"
        assert expected <= {h["fault_code"] for h in report["hypotheses"]}
    assert record["result"]["commands"] == [] and record["result"]["llm_calls"] == 0
    assert "generation" not in record["request"] and "scenario" not in record["request"]
    assert record["generation"]["conditions"]["workload"] == workload
    import json

    spec = GenerationMetadata.model_validate_json(json.dumps(record["generation"]))
    assert generate_operating_case(spec).window.model_dump(mode="json") == record["request"]["window"]
    replay = api.post("/api/v1/runs/" + record["run_id"] + "/replay", headers=writer).json()
    assert replay["matches"]
    assert replay["record"]["generation"] == record["generation"]


def test_dynamic_core_profile_and_reader_boundary(api, writer, reader):
    body = {"conditions": {}, "profile": "core6", "scenario": "fan_loss"}
    assert api.post("/api/v1/analyses/scenario", headers=reader, json=body).status_code == 403
    record = api.post("/api/v1/analyses/scenario", headers=writer, json=body).json()
    assert record["request"]["research"] is None and record["generation"] is not None


def test_invalid_dynamic_request_does_not_create_history(api, writer):
    result = api.post("/api/v1/analyses/scenario", headers=writer, json={"conditions": {"fan_response_s": 0}})
    assert result.status_code == 422
    assert api.get("/api/v1/incidents", headers=writer).json()["items"] == []


def test_reference_generator_remains_default(api, writer):
    record = api.post("/api/v1/analyses/scenario", headers=writer, json={}).json()
    assert record["generation"] is None
    assert {s["ambient_c"] for s in record["request"]["window"]["samples"]} == {30.0}
