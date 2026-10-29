import json
from pathlib import Path

from canovatwin.history import HistoryService
from canovatwin.persistence.models import RecordedAnalysis
from canovatwin.persistence.sqlite import SQLiteRepository


def test_sprint5_record_without_generation_can_be_loaded_and_replayed(tmp_path):
    root = Path(__file__).resolve().parents[2]
    raw = json.loads((root / "web/tests/fixtures/panel.json").read_text())["record"]
    assert "generation" not in raw
    record = RecordedAnalysis.model_validate_json(json.dumps(raw))
    with SQLiteRepository(tmp_path / "old-record.sqlite3", create=True) as repo:
        repo.save(record)
        replay = HistoryService(repo).replay(record.run_id)
        assert replay.matches
        assert replay.record.generation is None
        assert replay.record.request == record.request
