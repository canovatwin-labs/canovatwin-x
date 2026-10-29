import socket
from datetime import UTC, datetime

import pytest

from canovatwin.contracts import AnalysisRequest
from canovatwin.telemetry import Scenario, generate_case


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("Offline tests attempted a network connection")

    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "create_connection", denied)


@pytest.fixture
def case_factory():
    def make(scenario=Scenario.NORMAL, **kwargs):
        return generate_case(scenario, start=datetime(2026, 10, 28, tzinfo=UTC), **kwargs)

    return make


@pytest.fixture
def request_factory(case_factory):
    def make(scenario=Scenario.NORMAL, **kwargs):
        case = case_factory(scenario, **kwargs)
        return AnalysisRequest(window=case.window, as_of=case.observation_time)

    return make
