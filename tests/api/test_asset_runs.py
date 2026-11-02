def create(api, writer, **fields):
    response = api.post(
        "/api/v1/analyses/scenario",
        headers=writer,
        json={"count": 30, "start": "2026-11-02T00:00:00Z", "capture_history": False, **fields},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_asset_runs_include_distinct_incidents_and_replays_with_stable_paging(api, reader, writer):
    first = create(api, writer)
    second = create(api, writer, scenario="fan_loss")
    other = create(api, writer, asset_id="synthetic-unit-02")
    replay = api.post("/api/v1/runs/" + first["run_id"] + "/replay", headers=writer).json()["record"]
    before = api.get("/api/v1/assets/detail", headers=reader, params={"asset_id": "synthetic-unit-01"}).json()

    def page(offset):
        return api.get(
            "/api/v1/assets/runs",
            headers=reader,
            params={"asset_id": "synthetic-unit-01", "limit": 1, "offset": offset},
        ).json()["items"]

    assert [page(i)[0]["run_id"] for i in range(3)] == [replay["run_id"], second["run_id"], first["run_id"]]
    assert page(3) == []
    assert first["result"]["incident_id"] != second["result"]["incident_id"]
    assert other["run_id"] not in [page(i)[0]["run_id"] for i in range(3)]
    assert (
        api.get("/api/v1/assets/detail", headers=reader, params={"asset_id": "synthetic-unit-01"}).json()
        == before
    )


def test_asset_runs_auth_empty_unknown_and_query_validation(api, reader):
    assert api.get("/api/v1/assets/runs?asset_id=synthetic-unit-01").status_code == 401
    assert (
        api.get("/api/v1/assets/runs", headers=reader, params={"asset_id": "synthetic-unit-01"}).json()[
            "items"
        ]
        == []
    )
    assert api.get("/api/v1/assets/runs", headers=reader, params={"asset_id": "unknown"}).status_code == 404
    for params in (
        {},
        {"asset_id": "x", "limit": 101},
        {"asset_id": "x", "offset": -1},
        {"asset_id": "x" * 101},
    ):
        assert api.get("/api/v1/assets/runs", headers=reader, params=params).status_code == 422


def test_observed_unicode_and_sql_characters_remain_exact_asset_filters(api, reader, writer):
    record = create(api, writer)
    request = record["request"]
    identifier = "ünite/a?x=' OR 1=1--"
    request["window"]["asset_id"] = identifier
    saved = api.post("/api/v1/analyses", headers=writer, json={"request": request}).json()
    response = api.get("/api/v1/assets/runs", headers=reader, params={"asset_id": identifier})
    assert response.status_code == 200
    assert [run["run_id"] for run in response.json()["items"]] == [saved["run_id"]]
