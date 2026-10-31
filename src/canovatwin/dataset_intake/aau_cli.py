"""Offline adapter for the pinned AAU Zenodo v5 supplementary measurements."""

import argparse
import json
from pathlib import Path

from .aau import prepare_aau


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path, help="Directory with two unmodified Zenodo v5 CSV files")
    parser.add_argument("--source-offset", required=True, help="Declared fixed UTC offset, e.g. +02:00")
    parser.add_argument(
        "--output-dir", required=True, type=Path, help="New directory for derived data and reports"
    )
    args = parser.parse_args(argv)
    try:
        report = prepare_aau(args.source_dir, args.output_dir, source_offset=args.source_offset)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"AAU intake failed: {exc}\n")
    print(
        json.dumps(
            {
                "output_dir": str(args.output_dir),
                "exact_matches": report["exact_matches"],
                "rows_by_split": {part["split"]: part["rows"] for part in report["intake"]["partitions"]},
                "review_status": report["review"]["run"]["report"]["status"],
                "human_review_required": report["review"]["run"]["report"]["human_review_required"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
