"""
Forecasting Engine — HC-05 SurgeShield.

Orchestrates sequential and multi-step demand forecasting across all 12 districts,
computes calibrated prediction intervals, evaluates models via rolling validation,
and manages residual state for downstream allocation and surge detection.
"""

from __future__ import annotations

from typing import Any, Sequence
import numpy as np

from app.forecasting.metrics import compute_forecast_utility, compute_mae, compute_rmse
from app.forecasting.models import BaseForecaster, get_model
from app.forecasting.residuals import ResidualTracker, ResidualRecord
from app.forecasting.schemas import (
    DemandHistoryPoint,
    DistrictForecastResult,
    ForecastResponse,
    FutureForecastPoint,
    RiskLevel,
    ValidationMetricReport,
)
from app.forecasting.validator import RollingOriginValidator


def classify_risk(forecast: int, capacity: int) -> RiskLevel:
    """
    Standard risk classification based on expected capacity shortage gap:
        gap = forecast - capacity
        gap >= 30 -> Critical
        gap >= 15 -> High
        gap >= 5  -> Medium
        otherwise -> Low
    """
    gap = forecast - capacity
    if gap >= 30:
        return "Critical"
    if gap >= 15:
        return "High"
    if gap >= 5:
        return "Medium"
    return "Low"


class ForecastingEngine:
    """
    High-level facade and orchestrator for district demand forecasting.
    """

    def __init__(
        self,
        default_model: str = "harmonic_regression",
        residual_tracker: ResidualTracker | None = None,
    ):
        self.default_model = default_model
        self.residual_tracker = residual_tracker or ResidualTracker()
        self.validator = RollingOriginValidator(min_train_window=24, max_train_window=35)
        # district_id -> fitted forecaster
        self.fitted_models_: dict[str, BaseForecaster] = {}

    def forecast_district(
        self,
        district_id: str,
        history: Sequence[int] | np.ndarray,
        horizon: int = 6,
        capacity: int = 100,
        model_type: str | None = None,
        alpha: float = 0.10,
        start_month: int = 36,
    ) -> DistrictForecastResult:
        """
        Generate point forecast, trend, seasonality, and prediction intervals for a single district.
        """
        model_key = model_type or self.default_model
        forecaster = get_model(model_key)
        
        hist_arr = np.asarray(history, dtype=float).ravel()
        forecaster.fit(hist_arr)
        self.fitted_models_[district_id] = forecaster

        point, lower, upper = forecaster.predict_with_uncertainty(horizon=horizon, alpha=alpha)
        params = forecaster.get_params()

        trend = float(params.get("trend", 0.0))
        amplitude = float(params.get("seasonal_amplitude", params.get("amplitude", 0.0)))
        uncertainty = float(getattr(forecaster, "residual_std_", 8.0))

        # Build chronological history records
        history_points: list[DemandHistoryPoint] = []
        fitted_vals = getattr(forecaster, "fitted_values_", None)
        for t, act in enumerate(hist_arr):
            fc = int(fitted_vals[t]) if (fitted_vals is not None and t < len(fitted_vals)) else int(round(act))
            res = int(round(act - fc))
            history_points.append(
                DemandHistoryPoint(
                    district_id=district_id,
                    month=t,
                    actual=int(round(act)),
                    forecast=fc,
                    capacity=capacity,
                    residual=res,
                )
            )

        # Build future prediction points
        future_points: list[FutureForecastPoint] = []
        for h in range(horizon):
            m = start_month + h
            future_points.append(
                FutureForecastPoint(
                    month=m,
                    forecast=int(point[h]),
                    lower=int(lower[h]),
                    upper=int(upper[h]),
                    capacity=capacity,
                )
            )

        curr_fc = int(point[0]) if len(point) > 0 else 0
        risk = classify_risk(curr_fc, capacity)

        return DistrictForecastResult(
            district_id=district_id,
            current_forecast=curr_fc,
            trend_slope=round(trend, 3),
            seasonal_amplitude=round(amplitude, 2),
            uncertainty_std=round(uncertainty, 2),
            risk_level=risk,
            model_used=model_key,
            history=history_points,
            future=future_points,
            params=params,
        )

    def forecast_all_districts(
        self,
        historical_matrix: np.ndarray | dict[str, list[int]],
        capacities: dict[str, int] | Sequence[int] | None = None,
        district_ids: Sequence[str] | None = None,
        horizon: int = 6,
        start_month: int = 36,
        model_type: str | None = None,
        alpha: float = 0.10,
    ) -> ForecastResponse:
        """
        Produce synchronized forecasts for all 12 districts.
        """
        # Parse matrix and district IDs
        if isinstance(historical_matrix, dict):
            d_ids = list(historical_matrix.keys()) if district_ids is None else list(district_ids)
            data_dict = historical_matrix
        else:
            num_d = historical_matrix.shape[0]
            d_ids = [f"D{i}" for i in range(num_d)] if district_ids is None else list(district_ids)
            data_dict = {d_ids[i]: list(historical_matrix[i, :]) for i in range(len(d_ids))}

        # Parse capacities
        caps: dict[str, int] = {}
        if isinstance(capacities, dict):
            caps = capacities
        elif capacities is not None and len(capacities) == len(d_ids):
            caps = {d_ids[i]: int(capacities[i]) for i in range(len(d_ids))}
        else:
            caps = {d: 100 for d in d_ids}

        results: dict[str, DistrictForecastResult] = {}
        for d_id in d_ids:
            hist_series = data_dict[d_id]
            res = self.forecast_district(
                district_id=d_id,
                history=hist_series,
                horizon=horizon,
                capacity=caps.get(d_id, 100),
                model_type=model_type or self.default_model,
                alpha=alpha,
                start_month=start_month,
            )
            results[d_id] = res

        return ForecastResponse(
            status="success",
            start_month=start_month,
            horizon=horizon,
            model_used=model_type or self.default_model,
            districts=results,
        )

    def step_sequential(
        self,
        current_month: int,
        history_so_far: dict[str, list[int]],
        capacities: dict[str, int],
        observed_previous_demand: dict[str, int] | None = None,
        model_type: str | None = None,
    ) -> dict[str, DistrictForecastResult]:
        """
        Execute one step of the sequential decision cycle:
        1. If observed_previous_demand for (current_month - 1) is given, update the residual tracker.
        2. Fit models on history_so_far (strictly 0..current_month-1).
        3. Predict demand for current_month.
        """
        model_key = model_type or self.default_model

        # 1. Update residual tracker if previous actuals are provided
        if observed_previous_demand is not None and current_month > 0:
            prev_m = current_month - 1
            for d_id, actual_val in observed_previous_demand.items():
                prev_fc = self.fitted_models_.get(d_id)
                fc_val = getattr(prev_fc, "last_point_pred_", actual_val)
                self.residual_tracker.record(
                    district_id=d_id,
                    month=prev_m,
                    forecast=int(round(fc_val)),
                    actual=int(round(actual_val)),
                )

        # 2. Predict one step ahead for all districts
        results: dict[str, DistrictForecastResult] = {}
        for d_id, series in history_so_far.items():
            cap = capacities.get(d_id, 100)
            res = self.forecast_district(
                district_id=d_id,
                history=series,
                horizon=1,
                capacity=cap,
                model_type=model_key,
                start_month=current_month,
            )
            # Store point prediction for next step's residual evaluation
            model_inst = self.fitted_models_[d_id]
            model_inst.last_point_pred_ = res.current_forecast
            results[d_id] = res

        return results

    def validate_historical(
        self,
        historical_matrix: np.ndarray,
        models: Sequence[str] | None = None,
        district_ids: Sequence[str] | None = None,
    ) -> list[ValidationMetricReport]:
        """
        Run rolling origin cross-validation across all models on historical demand.
        """
        return self.validator.compare_models(
            demand_matrix=historical_matrix,
            models=models,
            district_ids=district_ids,
        )
