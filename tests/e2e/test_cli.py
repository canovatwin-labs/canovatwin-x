import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from canovatwin.cli import main
from canovatwin.contracts import AnalysisRequest


def test_command_line_subprocess():
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[2] / "src"))
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "canovatwin.cli",
            "--scenario",
            "fan_loss",
            "--format",
            "json",
            "--start",
            "2026-10-28T00:00:00+00:00",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    run = json.loads(result.stdout)
    assert run["report"]["status"] == "needs_review"
    assert run["commands"] == [] and run["llm_calls"] == 0
    assert len(run["trace"]) == 10


@pytest.mark.parametrize(
    "args",
    [[], ["--scenario", "fan_loss"], ["--scenario", "cooling_loss"], ["--registry"], ["--format", "json"]],
)
def test_cli_output_modes(monkeypatch, capsys, args):
    monkeypatch.setattr(sys, "argv", ["canovatwin", *args])
    assert main() == 0
    out = capsys.readouterr().out
    assert out
    if "--registry" in args:
        assert len(out.splitlines()) == 36
        assert "A02 | Sensor Validator | active" in out
        assert "D02 | Simulation Designer | active" in out
    elif "--format" in args:
        assert json.loads(out)["status"] == "completed"
    else:
        assert "CanovaTwin X" in out


def test_cli_input_document(request_factory, tmp_path, monkeypatch, capsys):
    path = tmp_path / "request.json"
    request = request_factory()
    assert AnalysisRequest.model_validate_json(request.model_dump_json()) == request
    path.write_text(request.model_dump_json())
    monkeypatch.setattr(sys, "argv", ["canovatwin", "--input", str(path), "--format", "json"])
    assert main() == 0
    assert json.loads(capsys.readouterr().out)["report"]["status"] == "clear"


@pytest.mark.parametrize(
    "args",
    [
        ["--count", "2"],
        ["--start", "bad"],
        ["--input", "/nonexistent/canovatwin.json"],
        ["--start", "2026-10-28"],
    ],
)
def test_cli_invalid_arguments(monkeypatch, capsys, args):
    monkeypatch.setattr(sys, "argv", ["canovatwin", *args])
    assert main() == 2
    assert "Invalid input" in capsys.readouterr().err


@pytest.mark.parametrize("text", ["private-secret-invalid-json", "x" * 2_000_001])
def test_cli_rejects_bad_files_without_echoing_data(tmp_path, monkeypatch, capsys, text):
    path = tmp_path / "bad.json"
    path.write_text(text)
    monkeypatch.setattr(sys, "argv", ["canovatwin", "--input", str(path)])
    assert main() == 2
    assert "private-secret" not in capsys.readouterr().err


def test_cli_blocked_run_returns_nonzero(monkeypatch, capsys):
    from canovatwin.agents import SensorValidator

    def fail(self, tools):
        raise RuntimeError("test")

    monkeypatch.setattr(SensorValidator, "execute", fail)
    monkeypatch.setattr(sys, "argv", ["canovatwin"])
    assert main() == 1
    assert "AGENT_EXECUTION_FAILED" in capsys.readouterr().out
