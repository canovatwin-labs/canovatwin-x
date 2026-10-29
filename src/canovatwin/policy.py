"""Explicit, bounded execution and demo-specific engineering assumptions."""

from pydantic import Field, model_validator

from .contracts import AnalysisRequest, Contract


class Policy(Contract):
    max_agents: int = Field(default=6, ge=1, le=12)
    max_tool_calls: int = Field(default=6, ge=1, le=20)
    max_tools_per_agent: int = Field(default=1, ge=1, le=5)
    max_elapsed_s: float = Field(default=5.0, gt=0, le=60)
    max_age_s: float = Field(default=60.0, ge=0)
    future_tolerance_s: float = Field(default=5.0, ge=0)
    max_gap_s: float = Field(default=5.0, gt=0)
    max_window_s: float = Field(default=3600.0, gt=0)
    high_inlet_c: float = 27.0
    temperature_rise_c: float = Field(default=1.0, gt=0)
    fan_error_pct: float = Field(default=10.0, gt=0, le=100)
    min_airflow_efficiency: float = Field(default=0.8, gt=0, le=1)
    min_cooling_efficiency: float = Field(default=0.8, gt=0, le=1)
    load_increase_kw: float = Field(default=1.0, gt=0)
    sensor_disagreement_c: float = Field(default=2.0, gt=0)
    fan_variation_pct: float = Field(default=25.0, gt=0, le=100)
    nominal_airflow_m3s: float = Field(default=2.5, gt=0)
    nominal_cooling_kw: float = Field(default=10.0, gt=0)

    @model_validator(mode="after")
    def sane_window(self):
        if self.max_gap_s > self.max_window_s:
            raise ValueError("max_gap_s cannot exceed max_window_s")
        return self


def default_policy(request: AnalysisRequest) -> Policy:
    return Policy(max_agents=12, max_tool_calls=12) if request.research is not None else Policy()
