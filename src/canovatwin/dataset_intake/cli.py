"""Validate a declared external CSV dataset without running diagnostics."""

import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from .models import DatasetManifest
from .validator import validate_dataset


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="JSON manifest containing CSV hashes and column units")
    parser.add_argument("--output", type=Path, help="Write report to a new file; stdout if omitted")
    args = parser.parse_args(argv)
    try:
        with args.manifest.open("rb") as stream:
            data = stream.read(1_000_001)
        if len(data) > 1_000_000:
            raise ValueError("Manifest exceeds 1 MB")
        manifest = DatasetManifest.model_validate_json(data)
        report = validate_dataset(manifest, args.manifest.resolve().parent)
        rendered = report.model_dump_json(indent=2) + "\n"
        if args.output is None:
            print(rendered, end="")
        else:
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(rendered)
        return 0
    except ValidationError as exc:
        print(
            "Invalid dataset manifest: " + "; ".join(e["msg"] for e in exc.errors(include_input=False)[:3]),
            file=sys.stderr,
        )
    except (OSError, ValueError) as exc:
        print(f"Dataset validation failed: {exc}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
