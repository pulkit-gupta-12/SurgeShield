"""
HC-05 SurgeShield — Forecasting Engine Package.
"""

from app.forecasting.metrics import (
    compute_forecast_utility,
    compute_mae,
    compute_rmse,
    compute_mape,
    evaluate_predictions,
)
from app.forecasting.models import (
    BaseForecaster,
    HarmonicRegressionForecaster,
    SeasonalNaiveForecaster,
    MovingAverageForecaster,
    ExponentialSmoothingForecaster,
    EnsembleForecaster,
    get_model,
    list_models,
)
from app.forecasting.residuals import ResidualTracker, ResidualRecord
from app.forecasting.validator import RollingOriginValidator
from app.forecasting.engine import ForecastingEngine, classify_risk
from app.forecasting.schemas import (
    DemandHistoryPoint,
    FutureForecastPoint,
    DistrictForecastResult,
    ForecastRequest,
    ForecastResponse,
    ValidationMetricReport,
    RiskLevel,
)

__all__ = [
    "compute_forecast_utility",
    "compute_mae",
    "compute_rmse",
    "compute_mape",
    "evaluate_predictions",
    "BaseForecaster",
    "HarmonicRegressionForecaster",
    "SeasonalNaiveForecaster",
    "MovingAverageForecaster",
    "ExponentialSmoothingForecaster",
    "EnsembleForecaster",
    "get_model",
    "list_models",
    "ResidualTracker",
    "ResidualRecord",
    "RollingOriginValidator",
    "ForecastingEngine",
    "classify_risk",
    "DemandHistoryPoint",
    "FutureForecastPoint",
    "DistrictForecastResult",
    "ForecastRequest",
    "ForecastResponse",
    "ValidationMetricReport",
    "RiskLevel",
]
