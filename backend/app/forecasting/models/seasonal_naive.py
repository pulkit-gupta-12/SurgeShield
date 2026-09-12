"""
Seasonal Naive Forecaster.
Benchmark model predicting y(t) = y(t - period).
"""

from __future__ import annotations

import math
from typing import Any, Sequence
import numpy as np

from app.forecasting.models.base import BaseForecaster


class SeasonalNaiveForecaster(BaseForecaster):
    """
    Seasonal Naive Forecaster for seasonal health demand.
    Repeats the value from exactly one seasonal cycle ago.
    """

    def __init__(self, period: int = 12, name: str = "SeasonalNaive"):
        super().__init__(name=name)
        self.period = int(period)
        self.history_: np.ndarray | None = None

    def fit(
        self,
        y: np.ndarray | Sequence[float],
        t: np.ndarray | Sequence[int] | None = None,
    ) -> SeasonalNaiveForecaster:
        y_arr = np.asarray(y, dtype=float).ravel()
        n = len(y_arr)
        if n < 1:
            raise ValueError("Seasonal naive requires at least 1 observation.")

        self.history_ = y_arr
        self.n_obs_ = n
        if t is not None:
            self.last_t_ = int(round(np.asarray(t, dtype=float).ravel()[-1]))
        else:
            self.last_t_ = n - 1

        # Estimate residual std from historical lag differences if N > period
        if n > self.period:
            diffs = y_arr[self.period:] - y_arr[:-self.period]
            self.residual_std_ = float(np.std(diffs))
        else:
            self.residual_std_ = float(np.std(np.diff(y_arr))) if n > 1 else 8.0

        self.is_fitted = True
        return self

    def predict(self, horizon: int = 1) -> np.ndarray:
        if not self.is_fitted or self.history_ is None:
            raise RuntimeError("Forecaster must be fitted before predict() is called.")
        if horizon < 1:
            raise ValueError(f"Horizon must be >= 1, got {horizon}.")

        preds = np.zeros(horizon, dtype=int)
        n = len(self.history_)
        for h in range(horizon):
            if n >= self.period:
                # Target the same month of the seasonal cycle
                lag_idx = n - self.period + (h % self.period)
                if lag_idx < n:
                    val = self.history_[lag_idx]
                else:
                    val = preds[lag_idx - n]
            else:
                val = self.history_[-1]
            preds[h] = max(0, int(round(val)))

        return preds

    def get_params(self) -> dict[str, Any]:
        params = super().get_params()
        params["period"] = self.period
        return params
