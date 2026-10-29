"""Exercise an installed API over real loopback HTTP; all temporary resources are cleaned up."""

import argparse
import json
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic, sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from canovatwin.api.settings import initialize_config
from canovatwin.telemetry import Scenario


class PanelAssets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "script":
            assert attributes.get("src"), "Panel must not contain inline scripts"
            self.paths.append(attributes["src"])
        if tag == "link" and attributes.get("rel") in ("stylesheet", "icon"):
            self.paths.append(attributes["href"])


def verify() -> dict:
    with TemporaryDirectory(prefix="CanovaTwin API test ") as temporary:
        directory = Path(temporary)
        config = directory / "api.json"
        initialize_config(config)
        private = json.loads(config.read_text())
        with socket.socket() as available:
            available.bind(("127.0.0.1", 0))
            private["port"] = available.getsockname()[1]
        config.write_text(json.dumps(private))
        base = f"http://127.0.0.1:{private['port']}"
        with (directory / "server.log").open("w") as log:
            server = subprocess.Popen(
                [sys.executable, "-I", "-m", "canovatwin.api.server", "--config", str(config)],
                cwd=directory,
                stdout=log,
                stderr=log,
            )
            try:
                deadline = monotonic() + 15
                while True:
                    try:
                        with urlopen(base + "/health", timeout=0.5) as response:
                            assert response.status == 200
                        break
                    except (URLError, TimeoutError):
                        if server.poll() is not None or monotonic() > deadline:
                            raise RuntimeError("Local API did not become ready") from None
                        sleep(0.05)

                def call(method, path, body=None, role="write", expected=200):
                    headers = {}
                    if role:
                        headers["Authorization"] = "Bearer " + private[role + "_token"]
                    data = None
                    if body is not None:
                        data = json.dumps(body).encode()
                        headers["Content-Type"] = "application/json"
                    request = Request(base + path, data=data, headers=headers, method=method)
                    try:
                        response = urlopen(request, timeout=10)
                    except HTTPError as error:
                        response = error
                    with response:
                        status = response.status
                        value = json.loads(response.read())
                    if status != expected:
                        raise RuntimeError(f"{method} {path}: HTTP {status}, expected {expected}")
                    return value

                call("GET", "/api/v1/incidents", role=None, expected=401)
                assert call("GET", "/api/v1/session", role="read")["role"] == "reader"
                assert call("GET", "/api/v1/session", role="write")["role"] == "writer"
                with urlopen(base + "/panel/", timeout=5) as response:
                    assert response.status == 200
                    assert "script-src 'self'" in response.headers["content-security-policy"]
                    assert response.headers["cache-control"] == "no-store"
                    markup = response.read().decode()
                parser = PanelAssets()
                parser.feed(markup)
                assert len(parser.paths) >= 3
                for path in parser.paths:
                    assert path.startswith("/panel/assets/")
                    with urlopen(base + path, timeout=5) as response:
                        asset = response.read()
                        assert response.status == 200 and asset
                        assert private["read_token"].encode() not in asset
                        assert private["write_token"].encode() not in asset
                call("POST", "/api/v1/analyses/scenario", {}, role="read", expected=403)
                ready = call("GET", "/api/v1/health", role="read")
                assert ready["application_version"] == version("canovatwin-x") == "0.7.0"
                assert ready["engine_version"] == "0.4.0"
                assert len(call("GET", "/api/v1/agents", role="read")) == 36
                first = last = None
                for profile in ("core6", "mvp12"):
                    for scenario in Scenario:
                        record = call(
                            "POST",
                            "/api/v1/analyses/scenario",
                            {
                                "scenario": scenario.value,
                                "profile": profile,
                                "start": "2026-10-28T00:00:00Z",
                                "capture_history": False,
                            },
                            expected=201,
                        )
                        assert record["result"]["status"] == "completed"
                        assert record["result"]["commands"] == [] and record["result"]["llm_calls"] == 0
                        first = first or record
                        last = record
                for workload in ("steady", "cyclic", "batch"):
                    for scenario in Scenario:
                        dynamic = call(
                            "POST",
                            "/api/v1/analyses/scenario",
                            {
                                "scenario": scenario.value,
                                "count": 360,
                                "conditions": {"workload": workload},
                                "capture_history": False,
                            },
                            expected=201,
                        )
                        assert dynamic["result"]["status"] == "completed"
                        assert dynamic["generation"]["conditions"]["workload"] == workload
                        assert "generation" not in dynamic["request"]
                dynamic_replay = call("POST", f"/api/v1/runs/{dynamic['run_id']}/replay", expected=201)
                assert dynamic_replay["matches"]
                assert dynamic_replay["record"]["generation"] == dynamic["generation"]
                direct = call("POST", "/api/v1/analyses", {"request": first["request"]}, expected=201)
                assert direct["request"] == first["request"]
                incident = last["result"]["incident_id"]
                for revision, target in ((1, "investigating"), (2, "closed")):
                    call(
                        "POST",
                        f"/api/v1/incidents/{incident}/status",
                        {"target": target, "expected_revision": revision, "reason": "Loopback HTTP test"},
                        expected=200,
                    )
                replay = call("POST", f"/api/v1/runs/{last['run_id']}/replay", expected=201)
                assert replay["matches"] and replay["record"]["request"] == last["request"]
                summary = call("GET", f"/api/v1/incidents/{incident}", role="read")
                assert summary["status"] == "closed" and summary["revision"] == 4
                assert call("GET", f"/api/v1/runs/{last['run_id']}", role="read") == last
                assert len(call("GET", f"/api/v1/incidents/{incident}/runs", role="read")["items"]) == 2
                assert len(call("GET", f"/api/v1/incidents/{incident}/audit", role="read")["items"]) == 5
                call(
                    "POST",
                    f"/api/v1/incidents/{incident}/status",
                    {"target": "open", "expected_revision": 3, "reason": "Stale"},
                    expected=409,
                )
                call("POST", "/api/v1/analyses/scenario", {"count": "120"}, expected=422)

                def concurrent(index):
                    return call(
                        "POST",
                        "/api/v1/analyses/scenario",
                        {"start": "2026-10-29T00:00:00Z", "capture_history": False},
                        expected=201,
                    )

                with ThreadPoolExecutor(max_workers=4) as pool:
                    records = list(pool.map(concurrent, range(4)))
                assert len({record["run_id"] for record in records}) == 4
                identifier = records[0]["result"]["incident_id"]
                assert call("GET", f"/api/v1/incidents/{identifier}", role="read")["run_count"] == 4
                schema = call("GET", "/openapi.json", role=None)
                assert schema["info"]["version"] == "0.7.0"
                assert len(schema["paths"]) == 13
                return {
                    "application_version": "0.7.0",
                    "engine_version": "0.4.0",
                    "scenario_profile_checks": 22,
                    "dynamic_scenario_workload_checks": 33,
                    "concurrent_writes": 4,
                    "panel_assets": len(parser.paths),
                    "checks": [
                        "authentication",
                        "reader/writer separation",
                        "strict JSON",
                        "history",
                        "lifecycle",
                        "replay",
                        "revision conflict",
                        "concurrent persistence",
                        "OpenAPI",
                    ],
                    "result": "passed",
                }
            finally:
                server.terminate()
                try:
                    server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(
        "Real loopback API checks passed: 22 reference + 33 dynamic combinations, auth, history, lifecycle, replay and four concurrent writes."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
