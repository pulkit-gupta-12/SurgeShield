"""
Ensemble Forecaster.
Blends candidate models with inverse-variance weights learned from historical fit.
"""

from __future__ import annotations

from typing import Any, Sequence
import numpy as np

from app.forecasting.models.base import BaseForecaster
from app.forecasting.models.harmonic_regression import HarmonicRegressionForecaster
from app.forecasting.models.seasonal_naive import SeasonalNaiveForecaster


class EnsembleForecaster(BaseForecaster):
    """
    Combines predictions from multiple candidate sub-models using
    weights inversely proportional to their historical MSE.
    """

    def __init__(
        self,
        models: list[BaseForecaster] | None = None,
        weights: list[float] | None = None,
        name: str = "Ensemble",
    ):
        super().__init__(name=name)
        if models is None:
            self.models = [
                HarmonicRegressionForecaster(),
                SeasonalNaiveForecaster(),
            ]
        else:
            self.models = models
        self.weights = weights
        self.learned_weights_: list[float] = []

    def fit(
        self,
        y: np.ndarray | Sequence[float],
        t: np.ndarray | Sequence[int] | None = None,
    ) -> EnsembleForecaster:
        y_arr = np.asarray(y, dtype=float).ravel()
        n = len(y_arr)
        if n < 4:
            raise ValueError("Ensemble requires at least 4 observations.")

        self.n_obs_ = n
        if t is not None:
            self.last_t_ = int(round(np.asarray(t, dtype=float).ravel()[-1]))
        else:
            self.last_t_ = n - 1

        mses = []
        for model in self.models:
            model.fit(y_arr, t=t)
            # Compute in-sample or rolling error
            std = getattr(model, "residual_std_", 8.0)
            mses.append(max(0.1, std ** 2))

        if self.weights is not None and len(self.weights) == len(self.models):
            w_sum = sum(self.weights)
            self.learned_weights_ = [w / w_sum for w in self.weights]
        else:
            # Inverse MSE weighting
            inv_mses = [1.0 / m for m in mses]
            total_inv = sum(inv_mses)
            self.learned_weights_ = [inv / total_inv for inv in inv_mses]

        # Aggregate residual standard deviation
        self.residual_std_ = float(np.sqrt(sum(w * m for w, m in zip(self.learned_weights_, mses))))
        self.is_fitted = True
        return self

    def predict(self, horizon: int = 1) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Forecaster must be fitted before predict() is called.")
        if horizon < 1:
            raise ValueError(f"Horizon must be >= 1, got {horizon}.")

        combined = np.zeros(horizon, dtype=float)
        for model, w in zip(self.models, self.learned_weights_):
            pred = model.predict(horizon=horizon)
            combined += w * pred

        return np.maximum(0, np.round(combined)).astype(int)

    def get_params(self) -> dict[str, Any]:
        params = super().get_params()
        params.update({
            "sub_models": [m.name for m in self.models],
            "weights": self.learned_weights_,
        })
        return params
