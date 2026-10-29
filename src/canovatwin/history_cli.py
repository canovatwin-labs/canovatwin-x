"""History subcommands do not open or create a database until explicitly requested."""

import argparse
import json
from pathlib import Path

from .formatting import render_text
from .history import HistoryService
from .persistence.models import IncidentStatus, Transition
from .persistence.sqlite import SQLiteRepository


def register_history(subparsers) -> None:
    parser = subparsers.add_parser("history", help="Inspect persisted analyses and incident lifecycle")
    commands = parser.add_subparsers(dest="history_command", required=True)
    for name in ("list", "show", "runs", "run", "audit", "transition", "replay"):
        command = commands.add_parser(name)
        command.add_argument("--db", type=Path, required=True, help="Existing local history database")
        command.add_argument("--format", choices=("text", "json"), default="text")
        if name in ("list", "runs", "audit"):
            command.add_argument("--limit", type=int, default=20)
            command.add_argument("--offset", type=int, default=0)
        if name == "list":
            command.add_argument("--status", choices=[s.value for s in IncidentStatus])
        elif name in ("run", "replay"):
            command.add_argument("run_id")
        else:
            command.add_argument("incident_id")
        if name in ("transition", "replay"):
            command.add_argument(
                "--actor", default="local-user", help="Local audit label; not authenticated identity"
            )
        if name == "transition":
            command.add_argument("--to", choices=[s.value for s in IncidentStatus], required=True)
            command.add_argument(
                "--revision", type=int, required=True, help="Revision shown in the latest incident summary"
            )
            command.add_argument("--reason", required=True)


def _emit(value, text: str, format_: str) -> None:
    if format_ == "json":
        content = (
            [item.model_dump(mode="json") for item in value]
            if isinstance(value, tuple)
            else value.model_dump(mode="json")
        )
        print(json.dumps(content, ensure_ascii=False))
    else:
        print(text)


def _incident_text(incident) -> str:
    return (
        f"{incident.incident_id} | {incident.asset_id} | {incident.status.value} | "
        f"revision={incident.revision} | runs={incident.run_count} | "
        f"latest={incident.latest_run_id} | result={incident.latest_report_status or incident.latest_analysis_status}"
    )


def run_history(args: argparse.Namespace) -> int:
    command = args.history_command
    with SQLiteRepository(args.db, read_only=command not in ("transition", "replay")) as repo:
        if command == "list":
            records = repo.list_incidents(
                status=IncidentStatus(args.status) if args.status else None,
                limit=args.limit,
                offset=args.offset,
            )
            _emit(
                records,
                "\n".join(_incident_text(record) for record in records) or "Kayıt bulunamadı.",
                args.format,
            )
        elif command == "show":
            incident = repo.get_incident(args.incident_id)
            _emit(incident, _incident_text(incident), args.format)
        elif command == "runs":
            records = repo.list_runs(args.incident_id, limit=args.limit, offset=args.offset)
            _emit(
                records,
                "\n".join(
                    f"{r.run_id} | {r.status} | {r.recorded_at.isoformat()} | replay_of={r.replay_of or '-'}"
                    for r in records
                )
                or "Kayıt bulunamadı.",
                args.format,
            )
        elif command == "run":
            record = repo.get_run(args.run_id)
            _emit(record, f"Kayıt: {record.run_id}\n" + render_text(record.result), args.format)
        elif command == "audit":
            events = repo.audit(args.incident_id, limit=args.limit, offset=args.offset)
            _emit(
                events,
                "\n".join(
                    f"{e.event_id} | {e.recorded_at.isoformat()} | {e.actor} | {e.action} | {e.reason} | revision={e.revision}"
                    for e in events
                )
                or "Kayıt bulunamadı.",
                args.format,
            )
        elif command == "transition":
            change = Transition(
                incident_id=args.incident_id,
                target=IncidentStatus(args.to),
                expected_revision=args.revision,
                actor=args.actor,
                reason=args.reason,
            )
            incident = repo.transition(change)
            _emit(incident, _incident_text(incident), args.format)
        elif command == "replay":
            outcome = HistoryService(repo).replay(args.run_id, actor=args.actor)
            text = (
                f"Önceki kayıt: {args.run_id}\nYeni kayıt: {outcome.record.run_id}\n"
                f"Sonuçlar eşleşiyor: {outcome.matches}\nFarklı alanlar: {', '.join(outcome.differences) or 'yok'}\n"
                + render_text(outcome.record.result)
            )
            _emit(outcome, text, args.format)
            return 0 if outcome.matches and outcome.record.result.status == "completed" else 1
    return 0
