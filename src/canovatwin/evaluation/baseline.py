"""Small, independent threshold comparator; no supervisor, policies or agent tools."""

from statistics import mean

from ..contracts import AnalysisRequest, FaultCode
from .models import Prediction


def predict_threshold(request: AnalysisRequest) -> Prediction:
    samples = request.window.samples
    if (request.as_of - samples[-1].timestamp).total_seconds() > 60:
        return Prediction(status="insufficient_data", predicted=(FaultCode.COMMUNICATION_LOSS,))
    fields = (
        "inlet_c",
        "reference_inlet_c",
        "fan_command_pct",
        "fan_feedback_pct",
        "airflow_m3s",
        "cooling_kw",
        "it_load_kw",
    )
    if any(sum(getattr(s, field) is None for s in samples) / len(samples) > 0.2 for field in fields):
        return Prediction(status="insufficient_data", predicted=(FaultCode.SENSOR_MISSING,))
    complete = [s for s in samples if all(getattr(s, field) is not None for field in fields)]
    if len(complete) < 3:
        return Prediction(status="insufficient_data")
    first, last = complete[: max(1, len(complete) // 3)], complete[-max(1, len(complete) // 3) :]
    faults = []
    if mean(abs(s.inlet_c - s.reference_inlet_c) for s in last) >= 2:
        faults.append(FaultCode.SENSOR_BIAS)
    if mean(s.it_load_kw for s in last) - mean(s.it_load_kw for s in first) >= 2:
        faults.append(FaultCode.LOAD_SURGE)
    if mean(abs(s.fan_command_pct - s.fan_feedback_pct) for s in last) >= 15:
        faults.extend((FaultCode.FAN_MISMATCH, FaultCode.FAN_LOSS))
    if mean(s.airflow_m3s / max(2.5 * s.fan_feedback_pct / 100, 0.01) for s in last) < 0.65:
        faults.append(FaultCode.AIRFLOW_RESTRICTION)
    if mean(s.cooling_kw / max(4 * s.airflow_m3s, 0.01) for s in last) < 0.65:
        faults.append(FaultCode.COOLING_LOSS)
    commands = [s.fan_command_pct for s in complete]
    directions = [b - a for a, b in zip(commands, commands[1:], strict=False) if abs(b - a) > 1]
    reversals = sum(a * b < 0 for a, b in zip(directions, directions[1:], strict=False))
    if max(commands) - min(commands) >= 40 and reversals >= 3:
        faults.append(FaultCode.CONTROL_OSCILLATION)
    alarm = bool(faults) or max(s.inlet_c for s in complete) >= 27
    return Prediction(status="needs_review" if alarm else "clear", predicted=tuple(faults))
