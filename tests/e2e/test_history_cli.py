import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from canovatwin.cli import main
from canovatwin.history import HistoryService
from canovatwin.persistence.sqlite import SQLiteRepository


@pytest.fixture
def saved(tmp_path, request_factory):
    path = tmp_path / "veri geçmişi #1.sqlite3"
    with SQLiteRepository(path, create=True) as repo:
        record = HistoryService(repo).analyze(request_factory())
    return path, record


def invoke(monkeypatch, capsys, args):
    monkeypatch.setattr(sys, "argv", ["canovatwin", *args])
    code = main()
    output = capsys.readouterr()
    return code, output


@pytest.mark.parametrize("format_", ["text", "json"])
def test_persistent_analysis_cli(tmp_path, monkeypatch, capsys, format_):
    path = tmp_path / "new" / "history.sqlite3"
    code, output = invoke(
        monkeypatch, capsys, ["analyze", "--scenario", "cooling_loss", "--db", str(path), "--format", format_]
    )
    assert code == 0 and path.is_file()
    with SQLiteRepository(path, read_only=True) as repo:
        assert len(repo.list_incidents()) == 1
    if format_ == "json":
        record = json.loads(output.out)
        assert record["result"]["report"]["status"] == "needs_review"
        assert record["run_id"].startswith("RUN-")
    else:
        assert "Kayıt: RUN-" in output.out


@pytest.mark.parametrize("command", ["list", "show", "runs", "run", "audit", "replay"])
@pytest.mark.parametrize("format_", ["text", "json"])
def test_history_reads_and_replay(saved, monkeypatch, capsys, command, format_):
    path, record = saved
    args = ["history", command, "--db", str(path), "--format", format_]
    if command in ("run", "replay"):
        args.append(record.run_id)
    elif command != "list":
        args.append(record.result.incident_id)
    code, output = invoke(monkeypatch, capsys, args)
    assert code == 0 and output.out
    if format_ == "json":
        data = json.loads(output.out)
        if command == "replay":
            assert data["matches"] is True
            assert data["record"]["replay_of"] == record.run_id
    else:
        assert "INC-" in output.out or "RUN-" in output.out or "analysis_saved" in output.out


def test_cli_transition_and_conflict(saved, monkeypatch, capsys):
    path, record = saved
    args = [
        "history",
        "transition",
        record.result.incident_id,
        "--db",
        str(path),
        "--to",
        "investigating",
        "--revision",
        "1",
        "--reason",
        "Sensör kayıtlarını inceliyorum",
        "--format",
        "json",
    ]
    code, output = invoke(monkeypatch, capsys, args)
    assert code == 0 and json.loads(output.out)["revision"] == 2
    code, output = invoke(monkeypatch, capsys, args)
    assert code == 3 and "[CONFLICT]" in output.err


def test_cli_filters_and_pagination(saved, monkeypatch, capsys):
    path, _ = saved
    code, output = invoke(
        monkeypatch, capsys, ["history", "list", "--db", str(path), "--status", "closed", "--format", "json"]
    )
    assert code == 0 and json.loads(output.out) == []
    code, output = invoke(monkeypatch, capsys, ["history", "list", "--db", str(path), "--limit", "0"])
    assert code == 2 and "Invalid input" in output.err
    code, output = invoke(monkeypatch, capsys, ["history", "list", "--db", str(path), "--offset", "1"])
    assert code == 0 and "Kayıt bulunamadı" in output.out


def test_history_missing_file_is_nonzero_and_does_not_create_it(tmp_path, monkeypatch, capsys):
    path = tmp_path / "missing.sqlite3"
    code, output = invoke(monkeypatch, capsys, ["history", "list", "--db", str(path)])
    assert code == 3 and "[NOT_FOUND]" in output.err
    assert not path.exists()


def test_plain_analysis_and_registry_do_not_create_database(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    code, _ = invoke(monkeypatch, capsys, ["--scenario", "normal"])
    assert code == 0 and list(tmp_path.iterdir()) == []
    path = tmp_path / "unused.sqlite3"
    code, _ = invoke(monkeypatch, capsys, ["--registry", "--db", str(path)])
    assert code == 0 and not path.exists()


def test_sqlite_failure_does_not_print_success_report(tmp_path, monkeypatch, capsys):
    path = tmp_path / "not-a-database.sqlite3"
    path.write_text("private-data")
    code, output = invoke(monkeypatch, capsys, ["analyze", "--db", str(path)])
    assert code == 3 and output.out == ""
    assert "private-data" not in output.err


def test_separate_processes_preserve_history_and_replay(tmp_path):
    database = tmp_path / "history.sqlite3"
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[2] / "src"))

    def run(*args):
        result = subprocess.run(
            [sys.executable, "-m", "canovatwin.cli", *args],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        return json.loads(result.stdout)

    original = run(
        "analyze",
        "--scenario",
        "fan_loss",
        "--db",
        str(database),
        "--format",
        "json",
        "--start",
        "2026-10-28T00:00:00+00:00",
    )
    records = run("history", "list", "--db", str(database), "--format", "json")
    assert len(records) == 1 and records[0]["latest_run_id"] == original["run_id"]
    loaded = run("history", "run", original["run_id"], "--db", str(database), "--format", "json")
    assert loaded == original
    replayed = run("history", "replay", original["run_id"], "--db", str(database), "--format", "json")
    assert replayed["matches"] and replayed["record"]["run_id"] != original["run_id"]
    runs = run(
        "history", "runs", original["result"]["incident_id"], "--db", str(database), "--format", "json"
    )
    assert len(runs) == 2
