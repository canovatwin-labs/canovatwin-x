"""Stable logical incident identity shared by runtime and persistence."""

from hashlib import sha256

from .contracts import AnalysisRequest
from .policy import Policy


def incident_identifier(request: AnalysisRequest, policy: Policy) -> str:
    serialized = request.model_dump_json(exclude={"research"} if request.research is None else None)
    digest = sha256((serialized + policy.model_dump_json()).encode()).hexdigest()[:16]
    return f"INC-{digest}"
