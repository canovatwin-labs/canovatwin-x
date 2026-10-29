"""Counterfactual thermal scenarios and explicit model-consistency validation."""

from math import sqrt
from statistics import fmean

from ..contracts import (
    FaultCode,
    SimulationAssessment,
    SimulationCase,
    SimulationResult,
    SimulationValidationResult,
)
from ..state import AnalysisContext
from .shared import evidence_for


def advance(
    temperature: float,
    load: float,
    cooling: float,
    ambient: float,
    capacity: float,
    conductance: float,
    dt: float,
) -> float:
    return temperature + (load + conductance * (ambient - temperature) - cooling) * dt / capacity


def design_simulation(ctx: AnalysisContext) -> SimulationResult:
    if ctx.request.research is None or ctx.quality is None or not ctx.quality.usable or ctx.critique is None:
        raise ValueError("Simulation requires valid telemetry and reviewed hypotheses")
    params = ctx.request.research.simulation
    samples = ctx.request.window.samples
    predicted = [samples[0].reference_inlet_c]
    for before, after in zip(samples[:-1], samples[1:], strict=True):
        predicted.append(
            advance(
                predicted[-1],
                before.it_load_kw,
                before.cooling_kw,
                before.ambient_c,
                params.thermal_capacity_kj_per_k,
                params.ambient_conductance_kw_per_k,
                (after.timestamp - before.timestamp).total_seconds(),
            )
        )
    n = max(1, len(samples) // 3)
    tail = samples[-n:]
    load, cooling, ambient = (
        fmean(getattr(s, key) for s in tail) for key in ("it_load_kw", "cooling_kw", "ambient_c")
    )
    initial = samples[-1].reference_inlet_c

    def final(load_, cooling_):
        temp = initial
        for _ in range(params.horizon_s):
            temp = advance(
                temp,
                load_,
                cooling_,
                ambient,
                params.thermal_capacity_kj_per_k,
                params.ambient_conductance_kw_per_k,
                1.0,
            )
        return temp

    baseline = final(load, cooling)
    eligible = {r.fault_code for r in ctx.critique.reviews if r.verdict != "weak"}
    signals = {e.metric: e.value for e in ctx.signals.evidence}
    scenarios = []
    if FaultCode.LOAD_SURGE in eligible:
        scenarios.append(
            ("restore_load", (FaultCode.LOAD_SURGE,), fmean(s.it_load_kw for s in samples[:n]), cooling)
        )
    if FaultCode.COOLING_LOSS in eligible:
        nominal = (
            fmean(s.airflow_m3s for s in tail)
            / ctx.policy.nominal_airflow_m3s
            * ctx.policy.nominal_cooling_kw
        )
        scenarios.append(("restore_cooling", (FaultCode.COOLING_LOSS,), load, nominal))
    fan_faults = tuple(code for code in (FaultCode.FAN_LOSS, FaultCode.FAN_MISMATCH) if code in eligible)
    if fan_faults:
        flow = (
            fmean(s.fan_command_pct for s in tail)
            / 100
            * ctx.policy.nominal_airflow_m3s
            * signals["airflow_efficiency"]
        )
        capacity = (
            flow
            / ctx.policy.nominal_airflow_m3s
            * ctx.policy.nominal_cooling_kw
            * signals["cooling_efficiency"]
        )
        scenarios.append(("restore_fan_tracking", fan_faults, load, capacity))
    if FaultCode.AIRFLOW_RESTRICTION in eligible:
        flow = fmean(s.fan_feedback_pct for s in tail) / 100 * ctx.policy.nominal_airflow_m3s
        capacity = (
            flow
            / ctx.policy.nominal_airflow_m3s
            * ctx.policy.nominal_cooling_kw
            * signals["cooling_efficiency"]
        )
        scenarios.append(("restore_airflow", (FaultCode.AIRFLOW_RESTRICTION,), load, capacity))
    # Counterfactual recovery stays within the declared unit's nominal capacity.
    scenarios = [
        (id_, codes, scenario_load, min(capacity, ctx.policy.nominal_cooling_kw))
        for id_, codes, scenario_load, capacity in scenarios
    ]
    cases = tuple(
        SimulationCase(
            scenario_id=id_,
            fault_codes=codes,
            load_kw=scenario_load,
            cooling_kw=scenario_cooling,
            final_c=final(scenario_load, scenario_cooling),
            reduction_vs_baseline_c=baseline - final(scenario_load, scenario_cooling),
        )
        for id_, codes, scenario_load, scenario_cooling in scenarios
    )
    metrics = {"baseline_final_c": (baseline, "degC")}
    metrics.update(
        {f"scenario_reduction_{i}": (case.reduction_vs_baseline_c, "degC") for i, case in enumerate(cases)}
    )
    return SimulationResult(
        predicted_reference_c=tuple(predicted),
        baseline_final_c=baseline,
        cases=cases,
        evidence=evidence_for(ctx, "D02", metrics, source="simulation"),
        limitation="Nominal kapasiteyle sınırlı, sabit son-pencere yük/debi varsayımına dayalı açık çevrim what-if hesabıdır; fiziksel müdahale veya nedensellik kanıtı değildir.",
    )


def validate_simulation(ctx: AnalysisContext) -> SimulationValidationResult:
    if ctx.simulation is None or ctx.request.research is None:
        raise ValueError("Validation requires a completed simulation")
    measured = [s.reference_inlet_c for s in ctx.request.window.samples]
    predicted = ctx.simulation.predicted_reference_c
    errors = [a - b for a, b in zip(measured, predicted, strict=True)]
    mae = fmean(abs(e) for e in errors)
    rmse = sqrt(fmean(e * e for e in errors))
    params = ctx.request.research.simulation
    adequate = mae <= params.max_mae_c and rmse <= params.max_rmse_c
    assessments = tuple(
        SimulationAssessment(
            scenario_id=case.scenario_id,
            assessment="illustrative_only"
            if not adequate
            else "reduction_in_model"
            if case.reduction_vs_baseline_c > 0.1
            else "no_material_reduction",
        )
        for case in ctx.simulation.cases
    )
    return SimulationValidationResult(
        mae_c=mae,
        rmse_c=rmse,
        model_adequate=adequate,
        assessments=assessments,
        evidence=evidence_for(
            ctx, "D06", {"model_mae_c": (mae, "degC"), "model_rmse_c": (rmse, "degC")}, source="simulation"
        ),
    )
