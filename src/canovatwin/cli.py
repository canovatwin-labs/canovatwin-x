"""Offline analysis plus explicit persistence; legacy demo flags stay supported."""

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from .contracts import AnalysisRequest, ResearchInputs, TechnicalDocument
from .formatting import render_text
from .history import HistoryService
from .history_cli import register_history, run_history
from .knowledge import demo_documents
from .persistence.errors import StorageError
from .persistence.sqlite import SQLiteRepository
from .registry import REGISTRY
from .snapshots import capture_history
from .supervisor import Supervisor
from .telemetry import Scenario, generate_case


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CanovaTwin X: offline synthetic fault investigation")
    commands = parser.add_subparsers(dest="command", required=True)
    analyze = commands.add_parser("analyze", help="Analyze a synthetic window; optionally persist results")
    analyze.add_argument(
        "--profile", choices=("core6", "mvp12"), help="Default: mvp12; JSON input controls its own profile"
    )
    analyze.add_argument("--knowledge", type=Path, help="Local JSON array of document snapshots")
    analyze.add_argument("--scenario", choices=[s.value for s in Scenario], default="normal")
    analyze.add_argument("--count", type=int, default=120)
    analyze.add_argument("--seed", type=int, default=42)
    analyze.add_argument("--start", help="Timezone-aware ISO 8601 replay start")
    analyze.add_argument("--format", choices=("text", "json"), default="text")
    analyze.add_argument("--input", type=Path, help="Read an AnalysisRequest JSON document")
    analyze.add_argument("--registry", action="store_true")
    analyze.add_argument(
        "--db", type=Path, help="Persist results to this SQLite database (created if missing)"
    )
    analyze.add_argument("--actor", default="local-user", help="Local audit label")
    register_history(commands)
    return parser


def _request(args: argparse.Namespace) -> AnalysisRequest:
    if args.input:
        if args.profile is not None or args.knowledge is not None:
            raise ValueError("JSON input already defines its research profile and sources")
        if args.input.stat().st_size > 2_000_000:
            raise ValueError("Input document exceeds 2 MB")
        return AnalysisRequest.model_validate_json(args.input.read_text())
    start = datetime.fromisoformat(args.start) if args.start else datetime.now(UTC)
    case = generate_case(Scenario(args.scenario), count=args.count, seed=args.seed, start=start)
    research = None
    if (args.profile or "mvp12") == "mvp12":
        documents = demo_documents()
        if args.knowledge:
            if args.knowledge.stat().st_size > 200000:
                raise ValueError("Knowledge input exceeds 200 KB")
            documents = TypeAdapter(tuple[TechnicalDocument, ...]).validate_json(args.knowledge.read_text())
        research = ResearchInputs(documents=documents)
    elif args.knowledge:
        raise ValueError("Knowledge input requires the mvp12 profile")
    return AnalysisRequest(window=case.window, as_of=case.observation_time, research=research)


def _analyze(args: argparse.Namespace) -> int:
    if args.registry:
        for spec in REGISTRY:
            print(
                f"{spec.agent_id} | {spec.name} | {spec.status} | stage={spec.activation_stage or 'unassigned'}"
            )
        return 0
    request = _request(args)
    if args.db:
        with SQLiteRepository(args.db, create=True) as repo:
            if not args.input:
                request = capture_history(repo, request)
            record = HistoryService(repo).analyze(request, actor=args.actor)
        print(
            record.model_dump_json()
            if args.format == "json"
            else f"Kayıt: {record.run_id}\n" + render_text(record.result)
        )
        return 0 if record.result.status == "completed" else 1
    run = Supervisor().run(request)
    print(run.model_dump_json() if args.format == "json" else render_text(run))
    return 0 if run.status == "completed" else 1


def main() -> int:
    arguments = sys.argv[1:]
    if not arguments or (arguments[0].startswith("-") and arguments[0] not in ("--help", "-h")):
        arguments = ["analyze", *arguments]
    args = _parser().parse_args(arguments)
    try:
        return run_history(args) if args.command == "history" else _analyze(args)
    except StorageError as exc:
        print(f"History error [{exc.code}]: {exc}", file=sys.stderr)
        return 3
    except (ValidationError, ValueError, OSError) as exc:
        print(
            f"Invalid input ({type(exc).__name__}); check schema, timestamps and arguments.", file=sys.stderr
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
