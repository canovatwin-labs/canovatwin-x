"""Start the local server or generate a private configuration without echoing secrets."""

import argparse
import sys
from pathlib import Path

import uvicorn
from pydantic import ValidationError

from ..persistence.errors import StorageError
from .app import create_app
from .settings import initialize_config, load_settings


def main() -> int:
    parser = argparse.ArgumentParser(description="CanovaTwin X local API")
    parser.add_argument("command", choices=("serve", "init"), nargs="?", default="serve")
    parser.add_argument("--config", type=Path, default=Path(".local/api-config.json"))
    args = parser.parse_args()
    try:
        if args.command == "init":
            initialize_config(args.config)
            print("Private API configuration created. Existing files are never overwritten.")
            return 0
        settings = load_settings(args.config)
        app = create_app(settings)
        uvicorn.run(app, host="127.0.0.1", port=settings.port, access_log=False)
        return 0
    except (OSError, ValidationError, ValueError, StorageError):
        print(
            "API configuration or startup failed; check the private configuration and database.",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
