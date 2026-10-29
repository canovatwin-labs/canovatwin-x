"""Export source API contracts for the typed local panel, without opening a database."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pydantic import SecretStr  # noqa: E402

from canovatwin.api.app import create_app  # noqa: E402
from canovatwin.api.settings import APISettings  # noqa: E402


def main() -> None:
    settings = APISettings(
        database=ROOT / ".local" / "schema-only-unused.sqlite3",
        read_token=SecretStr("schema-only-reader-" + "R" * 32),
        write_token=SecretStr("schema-only-writer-" + "W" * 32),
    )
    schema = create_app(settings).openapi()
    target = ROOT / "web" / "openapi.json"
    target.write_text(json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print("Panel OpenAPI contract exported; no database or private configuration used.")


if __name__ == "__main__":
    main()
