"""Audit the publisher-pinned Figshare hospital AHU CSV offline."""

import argparse
import sys
from pathlib import Path

from .figshare_hospital import audit_hospital_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Unmodified hosptial_scientific_data.csv")
    parser.add_argument("--output", type=Path, help="Write report to a new file; stdout if omitted")
    args = parser.parse_args(argv)
    try:
        report = audit_hospital_csv(args.source)
        rendered = report.model_dump_json(indent=2) + "\n"
        if args.output is None:
            print(rendered, end="")
        else:
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(rendered)
        return 0
    except (OSError, ValueError) as exc:
        print(f"Hospital audit failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
