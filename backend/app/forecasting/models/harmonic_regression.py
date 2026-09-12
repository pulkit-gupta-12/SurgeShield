"""
Harmonic Ordinary Least Squares (OLS) Regression Forecaster.

Exploits the exact mathematical structure of the HC-05 generator:
    μ(d,t) = b_d + g_d*t + a_d*sin(2πt/12 + dπ/6)
which is linear in four basis functions:
    y = β0 + β1*t + β2*sin(2πt/12) + β3*cos(2πt/12) + ε
where:
    β0 = b_d
    β1 = g_d
    β2 = a_d * cos(dπ/6)
    β3 = a_d * sin(dπ/6)

Under additive homoskedastic Gaussian noise N(0, 8²), this OLS estimator is
the Gauss-Markov Minimum Variance Linear Unbiased Estimator (MVLUE).
"""

from __future__ import annotations

import math
from typing import Any, Sequence
import numpy as np
from scipy.stats import norm, t as student_t

from app.forecasting.models.base import BaseForecaster


class HarmonicRegressionForecaster(BaseForecaster):
    """
    Harmonic OLS Regression forecaster for 12-month seasonal health demand with linear trend.
    """

    def __init__(self, period: float = 12.0, name: str = "HarmonicRegression"):
        super().__init__(name=name)
        self.period = float(period)
        self.beta_: np.ndarray | None = None
        self.cov_beta_: np.ndarray | None = None
        self.df_resid_: int = 0
        self.baseline_: float = 0.0
        self.trend_: float = 0.0
        self.amplitude_: float = 0.0
        self.phase_: float = 0.0
        self.fitted_values_: np.ndarray | None = None
        self.residuals_: np.ndarray | None = None

    def _build_design_matrix(self, t_arr: np.ndarray) -> np.ndarray:
        """Construct the [1, t, sin(2πt/L), cos(2πt/L)] design matrix."""
        omega = 2.0 * math.pi / self.period
        return np.column_stack([
            np.ones(len(t_arr)),
            t_arr,
            np.sin(omega * t_arr),
            np.cos(omega * t_arr),
        ])

    def fit(
        self,
        y: np.ndarray | Sequence[float],
        t: np.ndarray | Sequence[int] | None = None,
    ) -> HarmonicRegressionForecaster:
        """
        Fit harmonic regression via closed-form Ordinary Least Squares.
        
        Args:
            y: Observed demand series.
            t: Optional time indices. If None, 0..N-1 is used.
        """
        y_arr = np.asarray(y, dtype=float).ravel()
        n = len(y_arr)
        if n < 4:
            raise ValueError(f"Harmonic regression requires at least 4 observations, got {n}.")

        if t is None:
            t_arr = np.arange(n, dtype=float)
        else:
            t_arr = np.asarray(t, dtype=float).ravel()
            if len(t_arr) != n:
                raise ValueError(f"Length mismatch: len(y)={n} vs len(t)={len(t_arr)}.")

        X = self._build_design_matrix(t_arr)

        # Solve OLS via SVD-backed lstsq for robust inversion
        beta, residuals, rank, s = np.linalg.lstsq(X, y_arr, rcond=None)
        self.beta_ = beta

        fitted = X @ beta
        resid = y_arr - fitted
        df = max(1, n - 4)

        sse = float(np.sum(resid ** 2))
        mse = sse / df
        self.residual_std_ = math.sqrt(mse)
        self.df_resid_ = df

        # Parameter covariance matrix (X^T X)^(-1) * s^2
        try:
            xtx_inv = np.linalg.pinv(X.T @ X)
            self.cov_beta_ = xtx_inv * mse
        except Exception:
            self.cov_beta_ = np.eye(4) * mse

        # Extract structural parameters
        self.baseline_ = float(beta[0])
        self.trend_ = float(beta[1])
        beta2 = float(beta[2])
        beta3 = float(beta[3])
        self.amplitude_ = float(math.sqrt(beta2 ** 2 + beta3 ** 2))
        self.phase_ = float(math.atan2(beta3, beta2))

        self.fitted_values_ = np.round(fitted).astype(int)
        self.residuals_ = resid
        self.n_obs_ = n
        self.last_t_ = int(round(t_arr[-1]))
        self.is_fitted = True

        return self

    def predict(self, horizon: int = 1) -> np.ndarray:
        """Out-of-sample point predictions for the next `horizon` steps."""
        if not self.is_fitted or self.beta_ is None:
            raise RuntimeError("Forecaster must be fitted before predict() is called.")
        if horizon < 1:
            raise ValueError(f"Horizon must be >= 1, got {horizon}.")

        future_t = np.arange(self.last_t_ + 1, self.last_t_ + 1 + horizon, dtype=float)
        X_future = self._build_design_matrix(future_t)
        raw_pred = X_future @ self.beta_

        # Round to integers and clamp to non-negative
        return np.maximum(0, np.round(raw_pred)).astype(int)

    def predict_with_uncertainty(
        self,
        horizon: int = 1,
        alpha: float = 0.10,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Analytical prediction intervals accounting for both noise variance
        and parameter estimation uncertainty (leverage h_t = x_t (X^T X)^-1 x_t^T).
        """
        if not self.is_fitted or self.beta_ is None:
            raise RuntimeError("Forecaster must be fitted before predict_with_uncertainty().")

        future_t = np.arange(self.last_t_ + 1, self.last_t_ + 1 + horizon, dtype=float)
        X_future = self._build_design_matrix(future_t)
        point_raw = X_future @ self.beta_
        point = np.maximum(0, np.round(point_raw)).astype(int)

        # Critical value from Student's t or standard normal
        if self.df_resid_ >= 10:
            crit = student_t.ppf(1.0 - alpha / 2.0, df=self.df_resid_)
        else:
            crit = norm.ppf(1.0 - alpha / 2.0)

        # Prediction variance: s^2 * (1 + x_t (X^T X)^-1 x_t^T)
        lower = np.zeros(horizon, dtype=int)
        upper = np.zeros(horizon, dtype=int)

        s2 = self.residual_std_ ** 2
        for h in range(horizon):
            xh = X_future[h, :]
            if self.cov_beta_ is not None:
                var_pred = s2 + float(xh @ self.cov_beta_ @ xh.T)
            else:
                var_pred = s2
            se_pred = math.sqrt(max(1.0, var_pred))
            margin = crit * se_pred

            low_val = int(max(0, round(point_raw[h] - margin)))
            high_val = int(max(low_val, round(point_raw[h] + margin)))
            lower[h] = low_val
            upper[h] = high_val

        return point, lower, upper

    def get_params(self) -> dict[str, Any]:
        params = super().get_params()
        params.update({
            "period": self.period,
            "baseline": self.baseline_,
            "trend": self.trend_,
            "seasonal_amplitude": self.amplitude_,
            "phase_radians": self.phase_,
            "degrees_of_freedom": self.df_resid_,
            "coefficients": [float(b) for b in (self.beta_ if self.beta_ is not None else [])],
        })
        return params
