import json
import sys

import pytest

from canovatwin.cli import main
from canovatwin.contracts import ResearchInputs
from canovatwin.persistence.sqlite import SQLiteRepository


def invoke(monkeypatch, capsys, args):
    monkeypatch.setattr(sys, "argv", ["canovatwin", *args])
    code = main()
    return code, capsys.readouterr()


@pytest.mark.parametrize(("profile", "count"), [("core6", 6), ("mvp12", 10)])
def test_profiles_can_be_selected(monkeypatch, capsys, profile, count):
    code, out = invoke(
        monkeypatch, capsys, ["--profile", profile, "--scenario", "fan_loss", "--format", "json"]
    )
    assert code == 0
    run = json.loads(out.out)
    assert len(run["trace"]) == count
    assert (run["report"]["research"] is not None) == (profile == "mvp12")


def test_user_document_file_and_replay_are_snapshotted(tmp_path, monkeypatch, capsys):
    docs = tmp_path / "knowledge.json"
    docs.write_text(
        json.dumps(
            [
                {
                    "document_id": "USER-FAN",
                    "title": "Fan reference",
                    "version": "1",
                    "content": "fan airflow command feedback",
                }
            ]
        )
    )
    db = tmp_path / "history.sqlite3"
    code, out = invoke(
        monkeypatch,
        capsys,
        ["--scenario", "fan_loss", "--knowledge", str(docs), "--db", str(db), "--format", "json"],
    )
    assert code == 0
    original = json.loads(out.out)
    assert original["result"]["report"]["research"]["document_hits"][0]["document_id"] == "USER-FAN"
    docs.write_text("not JSON anymore")
    code, out = invoke(
        monkeypatch, capsys, ["history", "replay", original["run_id"], "--db", str(db), "--format", "json"]
    )
    assert code == 0 and json.loads(out.out)["matches"]


@pytest.mark.parametrize("problem", ["bad_json", "too_large", "core_profile", "wrong_hash"])
def test_bad_knowledge_input_is_rejected_without_creating_database(tmp_path, monkeypatch, capsys, problem):
    path = tmp_path / "knowledge.json"
    if problem == "too_large":
        path.write_text("x" * 200001)
    elif problem == "bad_json":
        path.write_text("private-source-content")
    else:
        path.write_text(
            json.dumps(
                [
                    {
                        "document_id": "x",
                        "title": "Fan",
                        "version": "1",
                        "content": "fan",
                        "content_hash": "0" * 64 if problem == "wrong_hash" else "",
                    }
                ]
            )
        )
    db = tmp_path / "never-created.sqlite3"
    args = ["--scenario", "fan_loss", "--knowledge", str(path), "--db", str(db)]
    if problem == "core_profile":
        args += ["--profile", "core6"]
    code, out = invoke(monkeypatch, capsys, args)
    assert code == 2 and not db.exists()
    assert "private-source-content" not in out.err


def test_explicit_request_is_not_augmented_from_live_sources(request_factory, tmp_path, monkeypatch, capsys):
    request = request_factory().model_copy(update={"research": ResearchInputs()})
    path = tmp_path / "request.json"
    path.write_text(request.model_dump_json())
    db = tmp_path / "history.sqlite3"
    code, out = invoke(monkeypatch, capsys, ["--input", str(path), "--db", str(db), "--format", "json"])
    assert code == 0
    record = json.loads(out.out)
    assert record["request"]["research"]["documents"] == []
    with SQLiteRepository(db, read_only=True) as repo:
        assert repo.get_run(record["run_id"]).request == request
    code, _ = invoke(monkeypatch, capsys, ["--input", str(path), "--profile", "mvp12"])
    assert code == 2
