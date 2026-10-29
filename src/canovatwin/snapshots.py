"""Capture historical inputs once, before execution; replay never reads live history."""

from .contracts import AnalysisRequest, HistoricalCase
from .persistence.repository import AnalysisRepository


def capture_history(repository: AnalysisRepository, request: AnalysisRequest) -> AnalysisRequest:
    if request.research is None or request.research.historical_cases:
        return request
    start = min(s.timestamp for s in request.window.samples)
    cases = []
    for incident in repository.list_incidents(limit=100):
        if incident.asset_id != request.window.asset_id or incident.latest_report_status != "needs_review":
            continue
        record = repository.get_run(incident.latest_run_id)
        end = max(s.timestamp for s in record.request.window.samples)
        if end >= start:
            continue
        cases.append(
            HistoricalCase(
                run_id=record.run_id,
                incident_id=record.result.incident_id,
                asset_id=record.request.window.asset_id,
                window_start=min(s.timestamp for s in record.request.window.samples),
                window_end=end,
                engine_version=record.engine_version,
                observation_codes=tuple(o.code for o in record.result.report.observations),
                candidate_faults=tuple(h.fault_code for h in record.result.report.hypotheses),
            )
        )
        if len(cases) == 20:
            break
    research = request.research.model_copy(update={"historical_cases": tuple(cases)})
    return request.model_copy(update={"research": research})
