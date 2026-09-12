"""
HC-05 SurgeShield — FastAPI Application.

Exposes REST APIs for:
- Phase 1: Synthetic Scenario Generation
- Phase 2: Demand Forecasting & Residual Tracking
- Phase 3: Predictive Risk & 60-Unit Emergency Reserve Allocation
- Phase 4: Online Residual Anomaly & Surge Detection
- Phase 5: Zero-Leakage Sequential Evaluation & Baseline Benchmarks
- Phase 6: Full Integration with the React Dashboard
"""

from __future__ import annotations

from typing import Any
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.generator import (
    generate_development_scenario,
    generate_scenario,
    DEFAULT_SEED,
)
from app.forecasting import (
    ForecastingEngine,
    ForecastRequest,
    ForecastResponse,
    ValidationMetricReport,
    list_models,
)
from app.allocation import (
    ReserveAllocator,
    AllocationResult,
    AllocationRequest,
    AllocationPolicy,
    assess_district_risk,
)
from app.surge import OnlineSurgeDetector, SurgeAlert
from app.evaluation import (
    SequentialEvaluator,
    SequentialEvaluationResult,
    CompetitionScorecard,
    benchmark_all_policies,
    summarize_benchmarks,
    PolicyBenchmarkComparison,
)
from app.simulation import (
    SimulationEngine,
    SimulationScenario,
    SimulationResult,
)

app = FastAPI(
    title="SurgeShield API",
    description="HC-05 District Health Surge Forecast & Allocation System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = ForecastingEngine()
allocator = ReserveAllocator()
surge_detector = OnlineSurgeDetector()
evaluator = SequentialEvaluator(
    forecasting_engine=engine,
    allocator=allocator,
    surge_detector=surge_detector,
)
simulator = SimulationEngine(allocator=allocator, forecaster=engine)

# District metadata mapping matching frontend constants
DISTRICT_METADATA: dict[str, dict[str, Any]] = {
    "D0": {"name": "Northgate", "region": "North", "population": 320000},
    "D1": {"name": "Riverside", "region": "South", "population": 280000},
    "D2": {"name": "Eastfield", "region": "East", "population": 410000},
    "D3": {"name": "Westport", "region": "West", "population": 250000},
    "D4": {"name": "Central", "region": "Central", "population": 360000},
    "D5": {"name": "Highland", "region": "North", "population": 290000},
    "D6": {"name": "Bayview", "region": "South", "population": 310000},
    "D7": {"name": "Pinecrest", "region": "East", "population": 270000},
    "D8": {"name": "Lakeside", "region": "West", "population": 340000},
    "D9": {"name": "Southgate", "region": "South", "population": 390000},
    "D10": {"name": "Fairmont", "region": "Central", "population": 260000},
    "D11": {"name": "Cliffside", "region": "East", "population": 300000},
}


def _format_frontend_forecast(d_res: Any) -> dict[str, Any]:
    """Format DistrictForecastResult into the exact camelCase structure expected by frontend."""
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


# ── System Health ─────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "SurgeShield API",
        "version": "1.0.0",
        "phase": "Phase 1-6 Complete",
        "models_available": list_models(),
    }


# ── District Metadata Endpoints ───────────────────────────────────────────────

@app.get("/api/districts")
async def get_districts(seed: int = Query(default=DEFAULT_SEED)):
    """Return all 12 districts with HC-05 generator parameters and demographic metadata."""
    scenario = generate_development_scenario(seed=seed)
    districts_list = []
    for d_id in scenario.districts:
        p = scenario.params[d_id]
        meta = DISTRICT_METADATA.get(d_id, {"name": f"District {d_id}", "region": "Central", "population": 300000})
        districts_list.append({
            "id": d_id,
            "name": meta["name"],
            "region": meta["region"],
            "population": meta["population"],
            "nominalCapacity": scenario.capacities[d_id],
            "baseDemand": p.b_d,
            "trend": round(p.g_d, 2),
            "seasonalityAmplitude": round(p.a_d, 2),
            "uncertainty": 8.0,
        })
    return districts_list


@app.get("/api/districts/{district_id}")
async def get_district(district_id: str, seed: int = Query(default=DEFAULT_SEED)):
    """Return details for a single district."""
    d_id = district_id.upper()
    districts = await get_districts(seed=seed)
    for d in districts:
        if d["id"] == d_id:
            return d
    raise HTTPException(status_code=404, detail=f"District {d_id} not found.")


@app.get("/api/districts/{district_id}/detail")
async def get_district_detail(
    district_id: str,
    seed: int = Query(default=DEFAULT_SEED),
    policy: str = Query(default="Surge Adaptive"),
):
    """Detailed district diagnostics for DistrictDetail page."""
    d_id = district_id.upper()
    scenario = generate_development_scenario(seed=seed)
    if d_id not in scenario.districts:
        raise HTTPException(status_code=404, detail=f"District {d_id} not found.")

    district_meta = (await get_district(d_id, seed=seed))
    fc_data = await get_district_forecast(d_id, seed=seed, model="harmonic_regression")
    alloc_data = await get_allocations(policy=policy, seed=seed, month=36)

    alloc_item = next((a for a in alloc_data.allocations if a.districtId == d_id), None)
    reserve_units = alloc_item.reserve if alloc_item else 0

    observed = scenario.future_demand[d_id][0]
    effective_cap = scenario.capacities[d_id] + reserve_units
    unmet = max(0, observed - effective_cap)
    service_level = max(0.0, 1.0 - (unmet / max(1, observed)))

    risk_eval = assess_district_risk(
        district_id=d_id,
        forecast=fc_data["currentForecast"],
        capacity=scenario.capacities[d_id],
        sigma=fc_data["uncertainty"],
        allocated_reserve=reserve_units,
    )

    return {
        "district": district_meta,
        "forecast": fc_data,
        "allocation": alloc_item,
        "observed": observed,
        "effectiveCapacity": effective_cap,
        "unmetDemand": unmet,
        "serviceLevel": round(service_level, 4),
        "shortageProbability": risk_eval.shortage_probability,
        "risk": risk_eval.risk_level,
    }


# ── Forecasting Endpoints ─────────────────────────────────────────────────────

@app.get("/api/forecasts")
async def get_forecasts(
    seed: int = Query(default=DEFAULT_SEED, description="Scenario seed"),
    model: str = Query(default="harmonic_regression", description="Forecasting model"),
):
    """Returns forecasts across all 12 districts conforming directly to frontend DistrictForecast[]."""
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

    model_key = model if isinstance(model, str) else "harmonic_regression"
    res = engine.forecast_district(
        district_id=d_id,
        history=hist_series,
        horizon=6,
        capacity=cap,
        model_type=model_key,
        start_month=36,
    )
    return _format_frontend_forecast(res)


@app.post("/api/forecast/predict", response_model=ForecastResponse)
async def predict_demand(req: ForecastRequest):
    """Predict demand given request parameters or custom historical demand overrides."""
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
    """Execute leakage-free rolling-origin cross-validation across candidate models."""
    scenario = generate_development_scenario(seed=seed)
    hist_matrix = scenario.get_historical_matrix()
    eval_models = models or ["harmonic_regression", "seasonal_naive", "moving_average", "ensemble"]
    return engine.validate_historical(
        historical_matrix=hist_matrix,
        models=eval_models,
        district_ids=scenario.districts,
    )


# ── Allocation Endpoints ──────────────────────────────────────────────────────

@app.get("/api/allocations", response_model=AllocationResult)
async def get_allocations(
    policy: str = Query(default="Surge Adaptive"),
    seed: int = Query(default=DEFAULT_SEED),
    month: int = Query(default=36),
):
    """Computes reserve allocation for the given policy at month t."""
    month_val = month if isinstance(month, int) else 36
    seed_val = seed if isinstance(seed, int) else DEFAULT_SEED
    policy_val = policy if isinstance(policy, str) else "Surge Adaptive"

    scenario = generate_development_scenario(seed=seed_val)
    districts = scenario.districts
    capacities = scenario.capacities

    # Obtain forecast for month
    hist_matrix = scenario.get_historical_matrix()
    fc_res = engine.forecast_all_districts(
        historical_matrix=hist_matrix,
        capacities=capacities,
        district_ids=districts,
        horizon=1,
        start_month=month_val,
    )
    fc_dict = {d: fc_res.districts[d].current_forecast for d in districts}
    sigma_dict = {d: fc_res.districts[d].uncertainty_std for d in districts}

    # Compute legitimate surge signals from past residuals strictly prior to month_val
    surge_signals = {d: 0.0 for d in districts}
    if policy_val == "Surge Adaptive" and month_val > 36:
        temp_detector = OnlineSurgeDetector()
        for m_idx in range(36, month_val):
            step = m_idx - 36
            if step < scenario.future_months:
                for d in districts:
                    act_prev = scenario.future_demand[d][step]
                    h_prior = list(scenario.historical_demand[d]) + [
                        scenario.future_demand[d][s] for s in range(step)
                    ]
                    fc_prev = engine.forecast_district(
                        district_id=d,
                        history=h_prior,
                        horizon=1,
                        capacity=capacities[d],
                        start_month=m_idx,
                    ).future[0].forecast
                    temp_detector.observe(d, m_idx, fc_prev, act_prev, capacities[d])
        surge_signals = temp_detector.get_surge_signals(districts)

    return allocator.allocate(
        district_ids=districts,
        forecasts=fc_dict,
        capacities=capacities,
        sigmas=sigma_dict,
        policy=policy_val,  # type: ignore
        reserve_budget=60,
        surge_signals=surge_signals,
    )


@app.post("/api/allocations/optimize", response_model=AllocationResult)
async def optimize_allocation(req: AllocationRequest):
    """Custom allocation optimization endpoint."""
    district_ids = list(req.forecasts.keys())
    return allocator.allocate(
        district_ids=district_ids,
        forecasts=req.forecasts,
        capacities=req.capacities,
        sigmas=req.uncertainties,
        policy=req.policy,
        reserve_budget=req.reserve_budget,
        surge_signals=req.surge_signals,
    )


# ── Surge Detection Endpoints ─────────────────────────────────────────────────

@app.get("/api/surge-alerts", response_model=list[SurgeAlert])
@app.get("/api/surge/alerts", response_model=list[SurgeAlert])
async def get_surge_alerts(seed: int = Query(default=DEFAULT_SEED)):
    """Returns active surge detection alerts for the current monitoring period."""
    scenario = generate_development_scenario(seed=seed)
    # Run online detector across history up to month 36
    surge_detector.reset()
    alerts = []
    for d in scenario.districts:
        fc = scenario.historical_demand[d][-1]
        act = scenario.historical_demand[d][-1]
        alert = surge_detector.observe(
            district_id=d,
            month=35,
            forecast=fc,
            actual=act,
            capacity=scenario.capacities[d],
        )
        alerts.append(alert)
    return surge_detector.get_all_alerts(scenario.districts)


@app.get("/api/surge-alerts/{district_id}/history")
@app.get("/api/surge/history/{district_id}")
async def get_surge_history(district_id: str, seed: int = Query(default=DEFAULT_SEED)):
    """Returns past 12-month residual tracking timeline and anomaly status for a district."""
    d_id = district_id.upper()
    scenario = generate_development_scenario(seed=seed)
    if d_id not in scenario.districts:
        raise HTTPException(status_code=404, detail=f"District {d_id} not found.")

    fc_res = engine.forecast_district(
        district_id=d_id,
        history=scenario.historical_demand[d_id],
        horizon=6,
        capacity=scenario.capacities[d_id],
        start_month=36,
    )

    history_points = []
    for h in fc_res.history[-12:]:
        history_points.append({
            "month": h.month,
            "actual": h.actual,
            "forecast": h.forecast,
            "residual": h.residual,
            "isAnomaly": abs(h.residual) >= (fc_res.uncertainty_std * 2.5),
        })

    return history_points


@app.get("/api/surge-residuals/{district_id}")
async def get_surge_residuals(district_id: str, seed: int = Query(default=DEFAULT_SEED)):
    """Returns residual history plus current observed/forecasted figures."""
    d_id = district_id.upper()
    scenario = generate_development_scenario(seed=seed)
    if d_id not in scenario.districts:
        raise HTTPException(status_code=404, detail=f"District {d_id} not found.")

    history_points = await get_surge_history(d_id, seed=seed)
    fc_res = await get_district_forecast(d_id, seed=seed)
    observed = scenario.future_demand[d_id][0]
    current_fc = fc_res["currentForecast"]

    return {
        "history": history_points,
        "currentObserved": observed,
        "currentForecast": current_fc,
        "currentResidual": observed - current_fc,
    }


# ── Performance & Evaluation Endpoints ────────────────────────────────────────

@app.get("/api/performance")
async def get_performance(
    seed: int = Query(default=DEFAULT_SEED),
    policy: str = Query(default="Surge Adaptive"),
):
    """Executes sequential evaluation on the scenario and returns official competition scorecard."""
    scenario = generate_development_scenario(seed=seed)
    res: SequentialEvaluationResult = evaluator.evaluate_scenario(
        scenario=scenario,
        policy=policy,  # type: ignore
    )
    sc = res.scorecard
    return {
        "forecastUtility": sc.forecastUtility,
        "demandServiceUtility": sc.demandServiceUtility,
        "worstDistrictService": sc.worstDistrictService,
        "compliance": {
            "reserveConstraint": sc.compliance.reserveConstraint,
            "integerAllocations": sc.compliance.integerAllocations,
            "noFutureLeakage": sc.compliance.noFutureLeakage,
            "reproducibleConfig": sc.compliance.reproducibleConfig,
        },
        "districtService": [{"districtId": d.districtId, "service": d.service} for d in sc.districtService],
        "unmetDemandTimeline": [
            {
                "month": t.month,
                "demand": t.demand,
                "capacity": t.capacity,
                "reserve": t.reserve,
                "unmet": t.unmet,
            }
            for t in sc.unmetDemandTimeline
        ],
    }


@app.get("/api/performance/baselines", response_model=list[PolicyBenchmarkComparison])
async def get_baseline_comparison(seed: int = Query(default=DEFAULT_SEED)):
    """Benchmarks all 5 policies side-by-side on the specified scenario."""
    scenario = generate_development_scenario(seed=seed)
    bench_results = benchmark_all_policies(scenario=scenario, evaluator=evaluator)
    return summarize_benchmarks(bench_results)


# ── Simulation Endpoints ──────────────────────────────────────────────────────

class SimulationPayload(BaseModel):
    scenario: SimulationScenario = "Baseline"
    seed: int = DEFAULT_SEED


@app.post("/api/simulation", response_model=list[SimulationResult])
async def run_simulation(payload: SimulationPayload = Body(default_factory=SimulationPayload)):
    """Runs what-if simulation across all 5 policies for the given scenario."""
    return simulator.run_scenario(
        scenario_type=payload.scenario,
        seed=payload.seed,
    )


@app.post("/api/simulation/sequential", response_model=SequentialEvaluationResult)
async def run_sequential_simulation(
    policy: str = Query(default="Surge Adaptive"),
    seed: int = Query(default=DEFAULT_SEED),
):
    """Executes full 6-month sequential simulation with complete audit cycle logs."""
    scenario = generate_development_scenario(seed=seed)
    return evaluator.evaluate_scenario(
        scenario=scenario,
        policy=policy,  # type: ignore
    )
