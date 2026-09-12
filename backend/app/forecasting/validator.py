"""
Leakage-Free Rolling-Origin Cross-Validation Engine.

Validates candidate forecasting models across strictly chronological origins (e.g. T=24..35),
guaranteeing zero future data leakage. Computes the official HC-05 forecast utility metric
alongside standard regression diagnostics.
"""

from __future__ import annotations

import time
from typing import Sequence
import numpy as np

from app.forecasting.metrics import (
    compute_forecast_utility,
    compute_mae,
    compute_rmse,
    compute_mape,
)
from app.forecasting.models import BaseForecaster, get_model, list_models
from app.forecasting.schemas import ValidationMetricReport


class RollingOriginValidator:
    """
    Evaluates forecasters using rolling-origin (time-series cross-validation) evaluation.
    
    Given historical series of length total_historical (e.g. 36), evaluates one-step
    predictions for origins T in [min_train_window .. total_historical - 1].
    """

    def __init__(
        self,
        min_train_window: int = 24,
        max_train_window: int = 35,
    ):
        self.min_train_window = int(min_train_window)
        self.max_train_window = int(max_train_window)

    def validate_single_series(
        self,
        series: np.ndarray | Sequence[float],
        model: BaseForecaster | str,
        origins: Sequence[int] | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Run rolling origin evaluation on a single 1D series.
        
        Returns:
            (actuals, predictions) out-of-sample arrays.
        """
        y_arr = np.asarray(series, dtype=float).ravel()
        n = len(y_arr)

        if origins is None:
            max_orig = min(n - 1, self.max_train_window)
            eval_origins = list(range(self.min_train_window, max_orig + 1))
        else:
            eval_origins = list(origins)

        if not eval_origins:
            raise ValueError(
                f"No valid evaluation origins for series of length {n} with min_window={self.min_train_window}."
            )

        actuals = []
        predictions = []

        for origin in eval_origins:
            if origin >= n:
                continue
            train_slice = y_arr[:origin]
            target = y_arr[origin]

            # Instantiate a fresh model instance per origin to guarantee zero state leakage
            forecaster = get_model(model) if isinstance(model, str) else model.__class__()
            forecaster.fit(train_slice)
            pred = forecaster.predict(horizon=1)[0]

            actuals.append(int(round(target)))
            predictions.append(int(round(pred)))

        return np.array(actuals, dtype=int), np.array(predictions, dtype=int)

    def validate_matrix(
        self,
        demand_matrix: np.ndarray,
        model: BaseForecaster | str,
        district_ids: Sequence[str] | None = None,
        origins: Sequence[int] | None = None,
    ) -> ValidationMetricReport:
        """
        Run rolling origin validation across all districts in demand_matrix (shape: num_districts, num_months).
        
        Returns:
            ValidationMetricReport with aggregated and per-district metrics.
        """
        matrix = np.asarray(demand_matrix, dtype=float)
        num_districts, total_months = matrix.shape

        if district_ids is None:
            d_ids = [f"D{d}" for d in range(num_districts)]
        else:
            d_ids = list(district_ids)

        model_name = model if isinstance(model, str) else model.name

        t0 = time.perf_counter()
        all_actuals = []
        all_predictions = []
        per_district_mae: dict[str, float] = {}
        per_district_util: dict[str, float] = {}

        for d_idx in range(num_districts):
            d_id = d_ids[d_idx]
            series = matrix[d_idx, :]
            acts, preds = self.validate_single_series(series, model=model, origins=origins)

            all_actuals.extend(acts)
            all_predictions.extend(preds)

            per_district_mae[d_id] = compute_mae(acts, preds)
            per_district_util[d_id] = compute_forecast_utility(acts, preds)

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        all_acts_arr = np.array(all_actuals, dtype=int)
        all_preds_arr = np.array(all_predictions, dtype=int)

        return ValidationMetricReport(
            model_name=model_name,
            u_forecast=compute_forecast_utility(all_acts_arr, all_preds_arr),
            mae=compute_mae(all_acts_arr, all_preds_arr),
            rmse=compute_rmse(all_acts_arr, all_preds_arr),
            mape=compute_mape(all_acts_arr, all_preds_arr),
            per_district_utility=per_district_util,
            per_district_mae=per_district_mae,
            runtime_ms=round(elapsed_ms, 2),
            num_evaluations=len(all_acts_arr),
        )

    def compare_models(
        self,
        demand_matrix: np.ndarray,
        models: Sequence[str] | None = None,
        district_ids: Sequence[str] | None = None,
    ) -> list[ValidationMetricReport]:
        """
        Evaluate and rank multiple candidate models on the exact same rolling-origin protocol.
        """
        if models is None:
            eval_models = ["harmonic_regression", "seasonal_naive", "moving_average", "ensemble"]
        else:
            eval_models = list(models)

        reports = []
        for m_name in eval_models:
            report = self.validate_matrix(demand_matrix, model=m_name, district_ids=district_ids)
            reports.append(report)

        # Sort descending by official competition utility U_forecast
        reports.sort(key=lambda r: r.u_forecast, reverse=True)
        return reports
