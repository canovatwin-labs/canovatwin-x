"""Explicit local configuration; secrets never belong to analysis inputs or responses."""

import json
import os
import re
from pathlib import Path
from secrets import token_urlsafe
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator

from ..contracts import Contract


class APISettings(Contract):
    database: Path
    read_token: SecretStr
    write_token: SecretStr
    allowed_origins: tuple[str, ...] = ()
    max_request_bytes: int = Field(default=2_000_000, ge=1024, le=2_000_000)
    port: int = Field(default=8000, ge=1024, le=65535)

    @field_validator("read_token", "write_token")
    @classmethod
    def valid_token(cls, value: SecretStr) -> SecretStr:
        if not re.fullmatch(r"[A-Za-z0-9_-]{32,256}", value.get_secret_value()):
            raise ValueError("Tokens must contain 32–256 URL-safe characters")
        return value

    @field_validator("allowed_origins")
    @classmethod
    def valid_origins(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        for value in values:
            if len(value) > 2048 or any(ord(character) <= 32 or ord(character) == 127 for character in value):
                raise ValueError("Origins cannot contain whitespace or control characters")
            parsed = urlsplit(value)
            if (
                parsed.scheme not in ("http", "https")
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.path
                or parsed.query
                or parsed.fragment
                or "*" in value
            ):
                raise ValueError("Each origin must be an explicit HTTP(S) origin without path or credentials")
            _ = parsed.port
        return tuple(dict.fromkeys(values))

    @model_validator(mode="after")
    def distinct_keys(self):
        if self.read_token.get_secret_value() == self.write_token.get_secret_value():
            raise ValueError("Reader and writer tokens must be distinct")
        return self


def load_settings(path: Path) -> APISettings:
    if path.stat().st_size > 16000:
        raise ValueError("API configuration exceeds 16 KB")
    settings = APISettings.model_validate_json(path.read_bytes())
    database = settings.database
    if not database.is_absolute():
        database = path.resolve().parent / database
    return settings.model_copy(update={"database": database})


def initialize_config(path: Path) -> None:
    """Exclusive creation prevents overwriting existing credentials."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        {
            "database": "history.sqlite3",
            "read_token": token_urlsafe(32),
            "write_token": token_urlsafe(32),
            "allowed_origins": [],
        },
        indent=2,
    )
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write(payload + "\n")
