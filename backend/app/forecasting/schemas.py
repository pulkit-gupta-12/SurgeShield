"""
Pydantic v2 schemas for HC-05 SurgeShield Forecasting Engine.
"""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


RiskLevel = Literal["Low", "Medium", "High", "Critical"]


class DemandHistoryPoint(BaseModel):
    """Historical or observed demand point."""
    district_id: str
    month: int
    actual: int
    forecast: int
    capacity: int = 0
    reserve: int = 0
    residual: int = 0


class FutureForecastPoint(BaseModel):
    """Forecast point for future planning month."""
    month: int
    forecast: int
    lower: int
    upper: int
    capacity: int = 0


class DistrictForecastResult(BaseModel):
    """Forecast and diagnostic state for a single district."""
    district_id: str
    current_forecast: int
    trend_slope: float
    seasonal_amplitude: float
    uncertainty_std: float
    risk_level: RiskLevel
    model_used: str
    history: list[DemandHistoryPoint] = Field(default_factory=list)
    future: list[FutureForecastPoint] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)


class ForecastRequest(BaseModel):
    """Request payload for multi-district forecasting."""
    seed: int = 20260911
    horizon: int = 6
    start_month: int = 36
    model_type: str = "harmonic_regression"
    alpha: float = 0.10
    history_override: dict[str, list[int]] | None = None


class ForecastResponse(BaseModel):
    """Response payload for multi-district forecasting."""
    status: str = "success"
    start_month: int
    horizon: int
    model_used: str
    districts: dict[str, DistrictForecastResult]
    validation_summary: dict[str, Any] | None = None


class ValidationMetricReport(BaseModel):
    """Evaluation summary for a model evaluated on rolling-origin cross-validation."""
    model_name: str
    u_forecast: float
    mae: float
    rmse: float
    mape: float
    per_district_utility: dict[str, float] = Field(default_factory=dict)
    per_district_mae: dict[str, float] = Field(default_factory=dict)
    runtime_ms: float = 0.0
    num_evaluations: int = 0
