# Implementation Plan — Phase 2: Forecasting Engine

Build the sequential demand forecasting engine for SurgeShield HC-05 across all 12 districts, maximizing competition forecast utility ($U_{\text{forecast}}$) while strictly adhering to sequential/online information constraints.

A full 30-section technical report has been generated at [`implementation_plan_phase2.md`](file:///c:/Users/PULKIT/OneDrive/Desktop/SurgeShield/implementation_plan_phase2.md).

## User Review Required

> [!IMPORTANT]
> **Primary Forecasting Model Decision: Harmonic OLS Regression vs SARIMA / Complex ML**
> 
> The demand-generation equation $\mu(d,t) = b_d + g_d t + a_d \sin(2\pi t/12 + d\pi/6)$ is mathematically linear in 4 parameters:
> $$\mu(d,t) = \beta_0 + \beta_1 t + \beta_2 \sin\left(\frac{2\pi t}{12}\right) + \beta_3 \cos\left(\frac{2\pi t}{12}\right)$$
> Under additive Gaussian noise $\varepsilon \sim \mathcal{N}(0, 8^2)$, **Ordinary Least Squares (OLS) is the Gauss-Markov Minimum Variance Linear Unbiased Estimator (MVLUE)**.
> - **Rolling Validation Performance ($t=24..35$, 144 evaluations):**
>   - Harmonic Regression: $\text{MAE} = 7.819$, $U_{\text{forecast}} = 0.9400$, runtime $< 0.1$ ms/fit.
>   - Seasonal Naive: $\text{MAE} = 13.257$, $U_{\text{forecast}} = 0.8982$.
>   - Statsmodels Holt-Winters / SARIMA: $> 40$ seconds runtime, numerical non-convergence risks on $N \le 36$.
> 
> Theoretical minimum MAE under $\sigma=8.0$ noise is $\mathbb{E}[|\varepsilon|] \approx 6.38$. Harmonic regression achieves near-optimal performance while executing in $<10$ ms for the entire 12-district system.

> [!IMPORTANT]
> **Database Decision**
> **No database (SQLite/PostgreSQL/ORM) will be introduced for Phase 2.** The forecasting system is a pure, deterministic, and reproducible in-memory pipeline. Pydantic models handle serialization for FastAPI and frontend consumption.

> [!IMPORTANT]
> **Residual Bias Correction Guardrail**
> Analysis demonstrates that applying rolling residual bias correction under normal noise degrades $U_{\text{forecast}}$ (chasing Gaussian noise). Therefore, baseline forecasting will predict the structural signal, while large positive residuals ($Z > 2.0$) are recorded in `ResidualTracker` and passed to Phase 4 (Surge Detection) rather than distorting baseline trend/seasonality.

---

## Proposed Changes

### Forecasting Subsystem (`backend/app/forecasting/`)

#### [NEW] [`schemas.py`](file:///c:/Users/PULKIT/OneDrive/Desktop/SurgeShield/backend/app/forecasting/schemas.py)
Pydantic v2 domain schemas (`DistrictForecastPoint`, `DistrictForecastResult`, `ForecastResponse`, `ForecastRequest`, `ValidationMetricReport`).

#### [NEW] [`metrics.py`](file:///c:/Users/PULKIT/OneDrive/Desktop/SurgeShield/backend/app/forecasting/metrics.py)
Exact competition metrics: $U_{\text{forecast}} = \max(0, 1 - \frac{\sum |y - \hat{y}|}{\sum \max(y, 1)})$, MAE, RMSE, MAPE.

#### [NEW] [`models/base.py`](file:///c:/Users/PULKIT/OneDrive/Desktop/SurgeShield/backend/app/forecasting/models/base.py)
Abstract base class `BaseForecaster` with `fit`, `predict`, and `predict_with_uncertainty`.

#### [NEW] [`models/harmonic_regression.py`](file:///c:/Users/PULKIT/OneDrive/Desktop/SurgeShield/backend/app/forecasting/models/harmonic_regression.py)
Primary OLS Harmonic Regression forecaster with closed-form parameter estimation, parameter recovery, and analytical prediction intervals.

#### [NEW] [`models/seasonal_naive.py`](file:///c:/Users/PULKIT/OneDrive/Desktop/SurgeShield/backend/app/forecasting/models/seasonal_naive.py)
Seasonal naive ($t-12$) baseline forecaster.

#### [NEW] [`models/moving_average.py`](file:///c:/Users/PULKIT/OneDrive/Desktop/SurgeShield/backend/app/forecasting/models/moving_average.py)
Local level / moving average forecaster over window $k$.

#### [NEW] [`models/exponential_smoothing.py`](file:///c:/Users/PULKIT/OneDrive/Desktop/SurgeShield/backend/app/forecasting/models/exponential_smoothing.py)
Exponential smoothing wrapper for comparison.

#### [NEW] [`models/ensemble.py`](file:///c:/Users/PULKIT/OneDrive/Desktop/SurgeShield/backend/app/forecasting/models/ensemble.py)
Inverse-variance weighted ensemble forecaster.

#### [NEW] [`models/__init__.py`](file:///c:/Users/PULKIT/OneDrive/Desktop/SurgeShield/backend/app/forecasting/models/__init__.py)
Model registry and factory method.

#### [NEW] [`residuals.py`](file:///c:/Users/PULKIT/OneDrive/Desktop/SurgeShield/backend/app/forecasting/residuals.py)
`ResidualTracker` tracking chronological residuals, rolling variance, and Z-score anomaly diagnostics for Phase 4.

#### [NEW] [`validator.py`](file:///c:/Users/PULKIT/OneDrive/Desktop/SurgeShield/backend/app/forecasting/validator.py)
`RollingOriginValidator` implementing leakage-free cross-validation across origins $T \in [24..35]$.

#### [NEW] [`engine.py`](file:///c:/Users/PULKIT/OneDrive/Desktop/SurgeShield/backend/app/forecasting/engine.py)
Top-level orchestrator coordinating forecasts, uncertainties, and model validation across all 12 districts.

#### [MODIFY] [`__init__.py`](file:///c:/Users/PULKIT/OneDrive/Desktop/SurgeShield/backend/app/forecasting/__init__.py)
Export public forecasting classes and utility functions.

#### [MODIFY] [`forecaster.py`](file:///c:/Users/PULKIT/OneDrive/Desktop/SurgeShield/backend/app/forecasting/forecaster.py)
Re-export `ForecastingEngine` for backward compatibility.

---

### API & Tests

#### [MODIFY] [`main.py`](file:///c:/Users/PULKIT/OneDrive/Desktop/SurgeShield/backend/app/main.py)
Wire FastAPI endpoints:
- `GET /api/forecasts`
- `GET /api/forecasts/{district_id}`
- `POST /api/forecast/predict`
- `POST /api/forecast/validate`

#### [NEW] [`test_forecasting.py`](file:///c:/Users/PULKIT/OneDrive/Desktop/SurgeShield/backend/tests/test_forecasting.py)
25+ comprehensive test cases covering:
1. Model mathematical correctness & parameter recovery
2. Leakage-free rolling validation
3. Competition metric $U_{\text{forecast}}$ exactness
4. Prediction interval bounds ($\text{lower} \le \hat{y} \le \text{upper}$, $\text{lower} \ge 0$)
5. Reproducibility & determinism
6. Integration with Phase 1 generator

---

### Frontend

#### [MODIFY] [`forecastService.ts`](file:///c:/Users/PULKIT/OneDrive/Desktop/SurgeShield/frontend/src/services/forecastService.ts)
Connect to `/api/forecasts` when `VITE_API_URL` is configured, with graceful fallback to `mockData.ts`.

---

## Verification Plan

### Automated Tests
- `pytest backend/tests -v`
  - Target: All 19 existing Phase 1 tests pass.
  - Target: All 25+ new Phase 2 forecasting tests pass.
  - Total: 44+ tests passing cleanly.

### Manual Verification
- Verify rolling-origin validation output shows $U_{\text{forecast}} \ge 0.930$.
- Test FastAPI `/api/forecasts` endpoint with `httpx` or `curl`.
- Verify frontend builds cleanly with `npm run build` in `frontend/`.
