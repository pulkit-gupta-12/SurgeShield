"""
Official HC-05 Competition Metrics and Regression Diagnostics.
"""

from __future__ import annotations

import numpy as np


def compute_forecast_utility(
    y_true: np.ndarray | list[float] | list[int],
    y_pred: np.ndarray | list[float] | list[int],
) -> float:
    """
    Computes the official HC-05 Forecast Utility metric:
        U_forecast = 1 - sum(|actual - forecast|) / sum(max(actual, 1))
    clipped to [0.0, 1.0].
    
    If inputs are empty, returns 0.0.
    """
    yt = np.asarray(y_true, dtype=float).ravel()
    yp = np.asarray(y_pred, dtype=float).ravel()

    if len(yt) == 0 or len(yp) == 0:
        return 0.0

    if len(yt) != len(yp):
        raise ValueError(f"Shape mismatch: y_true ({len(yt)}) vs y_pred ({len(yp)})")

    abs_errors = np.abs(yt - yp)
    denominators = np.maximum(yt, 1.0)
    
    sum_abs_err = float(np.sum(abs_errors))
    sum_denom = float(np.sum(denominators))

    if sum_denom <= 0.0:
        return 0.0

    utility = 1.0 - (sum_abs_err / sum_denom)
    return float(np.clip(utility, 0.0, 1.0))


def compute_mae(
    y_true: np.ndarray | list[float] | list[int],
    y_pred: np.ndarray | list[float] | list[int],
) -> float:
    """Mean Absolute Error."""
    yt = np.asarray(y_true, dtype=float).ravel()
    yp = np.asarray(y_pred, dtype=float).ravel()
    if len(yt) == 0:
        return 0.0
    return float(np.mean(np.abs(yt - yp)))


def compute_rmse(
    y_true: np.ndarray | list[float] | list[int],
    y_pred: np.ndarray | list[float] | list[int],
) -> float:
    """Root Mean Squared Error."""
    yt = np.asarray(y_true, dtype=float).ravel()
    yp = np.asarray(y_pred, dtype=float).ravel()
    if len(yt) == 0:
        return 0.0
    return float(np.sqrt(np.mean((yt - yp) ** 2)))


def compute_mape(
    y_true: np.ndarray | list[float] | list[int],
    y_pred: np.ndarray | list[float] | list[int],
) -> float:
    """Denominator-safe Mean Absolute Percentage Error (using max(actual, 1))."""
    yt = np.asarray(y_true, dtype=float).ravel()
    yp = np.asarray(y_pred, dtype=float).ravel()
    if len(yt) == 0:
        return 0.0
    denoms = np.maximum(yt, 1.0)
    return float(np.mean(np.abs(yt - yp) / denoms)) * 100.0


def evaluate_predictions(
    y_true: np.ndarray | list[float] | list[int],
    y_pred: np.ndarray | list[float] | list[int],
) -> dict[str, float]:
    """Computes all diagnostic metrics for a pair of prediction/actual arrays."""
    return {
        "u_forecast": compute_forecast_utility(y_true, y_pred),
        "mae": compute_mae(y_true, y_pred),
        "rmse": compute_rmse(y_true, y_pred),
        "mape": compute_mape(y_true, y_pred),
    }
