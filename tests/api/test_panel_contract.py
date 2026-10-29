import http.client
import json
from pathlib import Path

import pytest

from canovatwin.api.app import create_app
from canovatwin.persistence.models import RecordedAnalysis

ROOT = Path(__file__).resolve().parents[2]


def test_panel_openapi_snapshot_tracks_actual_source_api(api):
    saved = json.loads((ROOT / "web/openapi.json").read_text())
    assert saved == api.get("/openapi.json").json(), "Refresh the panel contract with npm run types"


@pytest.mark.parametrize(
    ("too_large", "unprocessable"),
    [
        ("Request Entity Too Large", "Unprocessable Entity"),  # Python 3.12
        ("Content Too Large", "Unprocessable Content"),  # Python 3.13+
    ],
)
def test_openapi_contract_is_independent_of_python_reason_phrases(
    api_settings, monkeypatch, too_large, unprocessable
):
    monkeypatch.setitem(http.client.responses, 413, too_large)
    monkeypatch.setitem(http.client.responses, 422, unprocessable)
    schema = create_app(api_settings).openapi()
    assert schema == json.loads((ROOT / "web/openapi.json").read_text())
    assert not api_settings.database.exists()


def test_ui_fixtures_are_valid_synthetic_records_not_invented_shapes():
    fixture = json.loads((ROOT / "web/tests/fixtures/panel.json").read_text())
    for key in ("record", "blocked", "insufficient"):
        record = RecordedAnalysis.model_validate_json(json.dumps(fixture[key]))
        assert record.request.window.source == "synthetic"
        assert record.result.commands == () and record.result.llm_calls == 0
    assert fixture["blocked"]["result"]["report"] is None
    assert fixture["insufficient"]["result"]["report"]["status"] == "insufficient_data"
