"""
HC-05 SurgeShield — FastAPI Application.

Exposes REST APIs for Phase 1 Scenario Generation, Phase 2 Demand Forecasting,
and sequential decision-making.
"""

from __future__ import annotations

from typing import Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.generator import generate_development_scenario, DEFAULT_SEED
from app.forecasting import (
    ForecastingEngine,
    ForecastRequest,
    ForecastResponse,
    ValidationMetricReport,
    list_models,
)

app = FastAPI(
    title="SurgeShield API",
    description="HC-05 District Health Surge Forecast & Allocation System",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = ForecastingEngine()


def _format_frontend_forecast(d_res: Any) -> dict[str, Any]:
    """Format DistrictForecastResult into the exact camelCase structure expected by the frontend."""
    return {
        "districtId": d_res.district_id,
        "currentForecast": d_res.current_forecast,
        "trend": d_res.trend_slope,
        "seasonality": d_res.seasonal_amplitude,
        "uncertainty": d_res.uncertainty_std,
        "risk": d_res.risk_level,
        "history": [
            {
                "districtId": h.district_id,
                "month": h.month,
                "actual": h.actual,
                "forecast": h.forecast,
                "capacity": h.capacity,
                "reserve": h.reserve,
                "residual": h.residual,
            }
            for h in d_res.history
        ],
        "future": [
            {
                "month": f.month,
                "forecast": f.forecast,
                "lower": f.lower,
                "upper": f.upper,
            }
            for f in d_res.future
        ],
    }


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "SurgeShield API",
        "version": "0.2.0",
        "phase": 2,
        "models_available": list_models(),
    }


@app.get("/api/forecasts")
async def get_forecasts(
    seed: int = Query(default=DEFAULT_SEED, description="Scenario seed"),
    model: str = Query(default="harmonic_regression", description="Forecasting model"),
):
    """
    Returns forecasts across all 12 districts conforming directly
    to the frontend DistrictForecast[] domain model.
    """
    scenario = generate_development_scenario(seed=seed)
    hist_matrix = scenario.get_historical_matrix()
    caps = scenario.capacities

    res = engine.forecast_all_districts(
        historical_matrix=hist_matrix,
        capacities=caps,
        district_ids=scenario.districts,
        horizon=6,
        start_month=36,
        model_type=model,
    )

    return [_format_frontend_forecast(res.districts[d]) for d in scenario.districts]


@app.get("/api/forecasts/{district_id}")
async def get_district_forecast(
    district_id: str,
    seed: int = Query(default=DEFAULT_SEED),
    model: str = Query(default="harmonic_regression"),
):
    """Get detailed forecast and uncertainty intervals for a single district."""
    scenario = generate_development_scenario(seed=seed)
    d_id = district_id.upper()
    if d_id not in scenario.districts:
        raise HTTPException(status_code=404, detail=f"District {d_id} not found.")

    hist_series = scenario.historical_demand[d_id]
    cap = scenario.capacities[d_id]

    res = engine.forecast_district(
        district_id=d_id,
        history=hist_series,
        horizon=6,
        capacity=cap,
        model_type=model,
        start_month=36,
    )

    return _format_frontend_forecast(res)


@app.post("/api/forecast/predict", response_model=ForecastResponse)
async def predict_demand(req: ForecastRequest):
    """
    Predict demand given request parameters or custom historical demand overrides.
    """
    if req.history_override is not None:
        hist_matrix = req.history_override
        caps = {d: 100 for d in hist_matrix.keys()}
        d_ids = list(hist_matrix.keys())
    else:
        scenario = generate_development_scenario(seed=req.seed)
        hist_matrix = scenario.get_historical_matrix()
        caps = scenario.capacities
        d_ids = scenario.districts

    return engine.forecast_all_districts(
        historical_matrix=hist_matrix,
        capacities=caps,
        district_ids=d_ids,
        horizon=req.horizon,
        start_month=req.start_month,
        model_type=req.model_type,
        alpha=req.alpha,
    )


@app.post("/api/forecast/validate", response_model=list[ValidationMetricReport])
async def validate_models(
    seed: int = Query(default=DEFAULT_SEED),
    models: list[str] | None = Query(default=None),
):
    """
    Execute leakage-free rolling-origin cross-validation (t=24..35) across candidate models.
    """
    scenario = generate_development_scenario(seed=seed)
    hist_matrix = scenario.get_historical_matrix()

    eval_models = models or ["harmonic_regression", "seasonal_naive", "moving_average", "ensemble"]
    return engine.validate_historical(
        historical_matrix=hist_matrix,
        models=eval_models,
        district_ids=scenario.districts,
    )
