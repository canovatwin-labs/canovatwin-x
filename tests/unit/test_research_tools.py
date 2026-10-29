from dataclasses import replace
from math import sqrt

import pytest
from pydantic import ValidationError

from canovatwin.analysis.research import (
    analyze_missing_data,
    critique_hypotheses,
    match_history,
    retrieve_documents,
)
from canovatwin.analysis.simulation import advance, design_simulation, validate_simulation
from canovatwin.contracts import ResearchInputs, SimulationParameters, SimulationResult, TechnicalDocument
from canovatwin.policy import Policy
from canovatwin.state import AnalysisContext


def test_independent_energy_balance_values():
    assert advance(25.0, 10.0, 5.0, 30.0, 100.0, 0.0, 2.0) == pytest.approx(25.1)
    assert advance(20.0, 0.0, 0.0, 30.0, 100.0, 1.0, 1.0) == pytest.approx(20.1)
    assert advance(25.0, 5.0, 5.0, 30.0, 100.0, 0.0, 2.0) == 25.0


def test_mae_rmse_with_hand_computed_errors(request_factory):
    base = request_factory()
    samples = tuple(
        s.model_copy(update={"reference_inlet_c": float(20 + i)})
        for i, s in enumerate(base.window.samples[:3])
    )
    request = base.model_copy(
        update={"window": base.window.model_copy(update={"samples": samples}), "research": ResearchInputs()}
    )
    ctx = AnalysisContext("INC-test", request, Policy())
    simulation = SimulationResult(
        predicted_reference_c=(20.0, 20.0, 20.0),
        baseline_final_c=20.0,
        cases=(),
        evidence=(),
        limitation="test",
    )
    result = validate_simulation(replace(ctx, simulation=simulation))
    assert result.mae_c == 1.0
    assert result.rmse_c == pytest.approx(sqrt(5 / 3))
    assert not result.model_adequate


@pytest.mark.parametrize(
    "tool",
    [
        analyze_missing_data,
        match_history,
        retrieve_documents,
        critique_hypotheses,
        design_simulation,
        validate_simulation,
    ],
)
def test_tools_require_upstream_context(request_factory, tool):
    ctx = AnalysisContext("INC-test", request_factory(), Policy())
    with pytest.raises(ValueError):
        tool(ctx)


@pytest.mark.parametrize(
    "change", [dict(horizon_s=121), dict(thermal_capacity_kj_per_k=0.0), dict(max_mae_c=float("nan"))]
)
def test_simulation_is_bounded(change):
    with pytest.raises(ValidationError):
        SimulationParameters(**change)


def test_document_limits_and_identity_are_strict():
    with pytest.raises(ValidationError):
        TechnicalDocument(document_id="x", title="x", version="1", content="x" * 12001)
    with pytest.raises(ValidationError):
        TechnicalDocument(document_id="x", title="x", version="1", content="safe", content_hash="0" * 64)
    doc = TechnicalDocument(document_id="x", title="x", version="1", content="safe")
    assert len(doc.content_hash) == 64
    with pytest.raises(ValidationError):
        ResearchInputs(documents=tuple(doc.model_copy(update={"document_id": str(i)}) for i in range(9)))
