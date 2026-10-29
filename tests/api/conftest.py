import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from canovatwin.api.app import create_app
from canovatwin.api.settings import APISettings


@pytest.fixture
def api_settings(tmp_path):
    return APISettings(
        database=tmp_path / "history.sqlite3",
        read_token=SecretStr("reader-token-" + "R" * 32),
        write_token=SecretStr("writer-token-" + "W" * 32),
    )


@pytest.fixture
def reader(api_settings):
    return {"Authorization": "Bearer " + api_settings.read_token.get_secret_value()}


@pytest.fixture
def writer(api_settings):
    return {"Authorization": "Bearer " + api_settings.write_token.get_secret_value()}


@pytest.fixture
def api(api_settings):
    with TestClient(create_app(api_settings), raise_server_exceptions=False) as client:
        yield client
