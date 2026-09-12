"""
Moving Average / Local Level Forecaster.
"""

from __future__ import annotations

from typing import Any, Sequence
import numpy as np

from app.forecasting.models.base import BaseForecaster


class MovingAverageForecaster(BaseForecaster):
    """
    Moving Average Forecaster predicting the mean of the most recent `window` observations.
    """

    def __init__(self, window: int = 3, name: str = "MovingAverage"):
        super().__init__(name=name)
        self.window = int(window)
        self.mean_value_: float = 0.0
        self.history_: np.ndarray | None = None

    def fit(
        self,
        y: np.ndarray | Sequence[float],
        t: np.ndarray | Sequence[int] | None = None,
    ) -> MovingAverageForecaster:
        y_arr = np.asarray(y, dtype=float).ravel()
        n = len(y_arr)
        if n < 1:
            raise ValueError("Moving average requires at least 1 observation.")

        self.history_ = y_arr
        self.n_obs_ = n
        if t is not None:
            self.last_t_ = int(round(np.asarray(t, dtype=float).ravel()[-1]))
        else:
            self.last_t_ = n - 1

        recent = y_arr[-self.window:] if n >= self.window else y_arr
        self.mean_value_ = float(np.mean(recent))

        if n > 1:
            # One-step rolling errors over history
            rolling_errors = []
            for i in range(1, n):
                w = min(i, self.window)
                prev_mean = np.mean(y_arr[i - w:i])
                rolling_errors.append(y_arr[i] - prev_mean)
            self.residual_std_ = float(np.std(rolling_errors)) if rolling_errors else 8.0
        else:
            self.residual_std_ = 8.0

        self.is_fitted = True
        return self

    def predict(self, horizon: int = 1) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Forecaster must be fitted before predict() is called.")
        if horizon < 1:
            raise ValueError(f"Horizon must be >= 1, got {horizon}.")

        val = max(0, int(round(self.mean_value_)))
        return np.full(horizon, val, dtype=int)

    def get_params(self) -> dict[str, Any]:
        params = super().get_params()
        params.update({"window": self.window, "mean_level": self.mean_value_})
        return params
