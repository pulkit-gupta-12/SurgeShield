"""
Forecaster — HC-05 SurgeShield.

Backward compatibility re-exports and direct forecaster service access.
"""

from app.forecasting.engine import ForecastingEngine, classify_risk
from app.forecasting.models.harmonic_regression import HarmonicRegressionForecaster
from app.forecasting.models.seasonal_naive import SeasonalNaiveForecaster
from app.forecasting.residuals import ResidualTracker
from app.forecasting.validator import RollingOriginValidator

__all__ = [
    "ForecastingEngine",
    "HarmonicRegressionForecaster",
    "SeasonalNaiveForecaster",
    "ResidualTracker",
    "RollingOriginValidator",
    "classify_risk",
]
