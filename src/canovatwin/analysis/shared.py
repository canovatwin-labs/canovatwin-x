"""Evidence identifiers bind derived values to this incident and source window."""

from ..contracts import Evidence
from ..state import AnalysisContext


def evidence_for(
    ctx: AnalysisContext, producer: str, metrics: dict[str, tuple[float, str]], *, source=None
) -> tuple[Evidence, ...]:
    source = source or ctx.request.window.source
    refs = tuple(s.sample_id for s in ctx.request.window.samples)
    return tuple(
        Evidence(
            evidence_id=f"EV-{ctx.incident_id[4:]}-{producer}-{key}",
            producer=producer,
            metric=key,
            value=value,
            unit=unit,
            sample_ids=refs,
            source=source,
        )
        for key, (value, unit) in metrics.items()
    )
