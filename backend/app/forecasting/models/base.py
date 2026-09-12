"""
Abstract Base Class for all forecasting models.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
import numpy as np


class BaseForecaster(ABC):
    """Abstract interface defining the contract for all district health forecasters."""

    def __init__(self, name: str = "BaseForecaster"):
        self.name = name
        self.is_fitted: bool = False
        self.n_obs_: int = 0
        self.last_t_: int = 0
        self.residual_std_: float = 8.0  # default fallback prior

    @abstractmethod
    def fit(self, y: np.ndarray | Sequence[float], t: np.ndarray | Sequence[int] | None = None) -> BaseForecaster:
        """
        Fit the forecasting model to historical demand series.
        
        Args:
            y: 1D array of observed demand values.
            t: Optional 1D array of time indices corresponding to y. If None, np.arange(len(y)) is used.
        """
        pass

    @abstractmethod
    def predict(self, horizon: int = 1) -> np.ndarray:
        """
        Produce out-of-sample point forecasts for the next `horizon` months.
        
        Returns:
            1D array of integer or rounded float forecasts, clamped to >= 0.
        """
        pass

    def predict_with_uncertainty(
        self,
        horizon: int = 1,
        alpha: float = 0.10,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Produce point forecasts and (1 - alpha) prediction intervals.
        
        Default implementation computes Gaussian bounds:
            [forecast - z * std, forecast + z * std]
        clamped to non-negative integers.
        
        Returns:
            (point_forecasts, lower_bounds, upper_bounds)
        """
        from scipy.stats import norm

        point = self.predict(horizon=horizon)
        z = norm.ppf(1.0 - alpha / 2.0)
        margin = z * max(1.0, self.residual_std_)

        lower = np.maximum(0, np.round(point - margin)).astype(int)
        upper = np.maximum(lower, np.round(point + margin)).astype(int)

        return point, lower, upper

    def fit_predict(
        self,
        y: np.ndarray | Sequence[float],
        horizon: int = 1,
        t: np.ndarray | Sequence[int] | None = None,
    ) -> np.ndarray:
        """Convenience method fitting on y and predicting horizon."""
        self.fit(y, t=t)
        return self.predict(horizon=horizon)

    def get_params(self) -> dict[str, Any]:
        """Return model hyperparameters and learned coefficients."""
        return {
            "name": self.name,
            "is_fitted": self.is_fitted,
            "n_obs": self.n_obs_,
            "residual_std": float(self.residual_std_),
        }
