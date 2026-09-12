"""
Forecasting Models Package.
Exports candidate forecasters and a centralized model factory.
"""

from __future__ import annotations

from app.forecasting.models.base import BaseForecaster
from app.forecasting.models.harmonic_regression import HarmonicRegressionForecaster
from app.forecasting.models.seasonal_naive import SeasonalNaiveForecaster
from app.forecasting.models.moving_average import MovingAverageForecaster
from app.forecasting.models.exponential_smoothing import ExponentialSmoothingForecaster
from app.forecasting.models.ensemble import EnsembleForecaster

MODEL_REGISTRY: dict[str, type[BaseForecaster]] = {
    "harmonic_regression": HarmonicRegressionForecaster,
    "seasonal_naive": SeasonalNaiveForecaster,
    "moving_average": MovingAverageForecaster,
    "exponential_smoothing": ExponentialSmoothingForecaster,
    "ensemble": EnsembleForecaster,
}


def get_model(name: str = "harmonic_regression", **kwargs) -> BaseForecaster:
    """Instantiate a forecaster from the registry by name."""
    normalized_name = name.lower().replace("-", "_").replace(" ", "_")
    if normalized_name not in MODEL_REGISTRY:
        available = list(MODEL_REGISTRY.keys())
        raise KeyError(f"Unknown model '{name}'. Available models: {available}")
    return MODEL_REGISTRY[normalized_name](**kwargs)


def list_models() -> list[str]:
    """List all registered model keys."""
    return list(MODEL_REGISTRY.keys())


__all__ = [
    "BaseForecaster",
    "HarmonicRegressionForecaster",
    "SeasonalNaiveForecaster",
    "MovingAverageForecaster",
    "ExponentialSmoothingForecaster",
    "EnsembleForecaster",
    "MODEL_REGISTRY",
    "get_model",
    "list_models",
]
