from canovatwin.persistence.sqlite import SQLiteRepository


def create_run(api, writer, **overrides):
    response = api.post(
        "/api/v1/analyses/stream",
        headers=writer,
        json={"start": "2026-10-31T00:00:00Z", "scenario": "fan_loss", **overrides},
    )
    assert response.status_code == 201, response.text
    return response.json()


def compare(api, reader, before, after):
    return api.get(
        "/api/v1/comparisons",
        headers=reader,
        params={"baseline": before["run_id"], "candidate": after["run_id"]},
    )


def test_compare_transport_profiles_is_read_only_and_reports_unaligned_windows(
    api, reader, writer, api_settings
):
    before = create_run(api, writer)
    after = create_run(api, writer, delivery="outage")
    with SQLiteRepository(api_settings.database, read_only=True) as repo:
        audit_before = repo.audit(before["result"]["incident_id"])
        audit_after = repo.audit(after["result"]["incident_id"])
    response = compare(api, reader, before, after)
    assert response.status_code == 200, response.text
    value = response.json()
    assert value["comparison_version"] == "comparison-1.0"
    assert value["baseline"]["transport_dropped"] == 0
    assert value["candidate"]["transport_dropped"] > 0
    assert value["same_measurement_timestamps"] is False
    assert "transport" in value["differing_inputs"]
    assert len(value["channels"]) == 11 and len(value["limitations"]) == 5
    cooling = next(channel for channel in value["channels"] if channel["field"] == "cooling_kw")
    assert cooling["unit"] == "kW"
    assert all(
        c["candidate"]["valid_count"] + c["candidate"]["missing_count"] == value["candidate"]["sample_count"]
        for c in value["channels"]
    )
    assert compare(api, reader, before, after).json() == value
    assert "actor" not in response.text and "write_token" not in response.text
    with SQLiteRepository(api_settings.database, read_only=True) as repo:
        assert repo.audit(before["result"]["incident_id"]) == audit_before
        assert repo.audit(after["result"]["incident_id"]) == audit_after


def test_compare_replay_preserves_zero_deltas_and_inputs(api, reader, writer):
    before = create_run(api, writer)
    replay = api.post("/api/v1/runs/" + before["run_id"] + "/replay", headers=writer).json()
    value = compare(api, reader, before, replay["record"]).json()
    assert value["differing_inputs"] == []
    assert value["same_measurement_timestamps"] is True
    assert all(channel["mean_delta"] == 0 and channel["final_delta"] == 0 for channel in value["channels"])


def test_compare_rejects_different_assets_same_record_and_unknown_runs(api, reader, writer):
    before = create_run(api, writer)
    after = create_run(api, writer, asset_id="synthetic-unit-02")
    for right in (before, after):
        response = compare(api, reader, before, right)
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "COMPARISON_INCOMPATIBLE"
    assert compare(api, reader, before, {"run_id": "RUN-unknown"}).status_code == 404


def test_compare_requires_authentication_and_valid_bounded_identifiers(api, reader):
    assert api.get("/api/v1/comparisons?baseline=x&candidate=y").status_code == 401
    for params in (
        {},
        {"baseline": "x", "candidate": "x" * 101},
        {"baseline": "' OR 1=1--", "candidate": "y"},
    ):
        assert api.get("/api/v1/comparisons", params=params, headers=reader).status_code == 422
