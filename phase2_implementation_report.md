# SURGESHIELD — HC-05: PHASE 2 IMPLEMENTATION REPORT
## Demand Forecasting Engine, Leakage-Free Rolling Validation, and Uncertainty Estimation

**Project:** SurgeShield — HC-05 District Health Surge Forecast and Allocation  
**Phase:** 2 — Forecasting Engine  
**Status:** IMPLEMENTATION COMPLETE & VERIFIED  
**Date:** September 12, 2026  
**Author:** Antigravity AI  

---

## 1. Implementation Summary

Phase 2 of SurgeShield has been fully implemented, tested, and empirically validated. It establishes the complete **District Health Demand Forecasting Engine** for all 12 synthetic districts ($D0$ through $D11$), connecting the Phase 1 Synthetic Data Generator to future allocation, surge detection, and evaluation layers.

Key achievements:
- Implemented the primary closed-form **Harmonic OLS Regression** forecaster, exploiting the mathematical structure of the HC-05 demand-generating equation.
- Built a leakage-free **Rolling-Origin Cross-Validator** ($T \in [24..35]$) evaluating 144 out-of-sample decision points across all 12 districts.
- Implemented the exact competition metric $U_{\text{forecast}} = \max\left(0, 1 - \frac{\sum |y - \hat{y}|}{\sum \max(y, 1)}\right)$.
- Achieved an empirical competition forecast utility of **$U_{\text{forecast}} = 0.9400$** (MAE: $7.819$), approaching the theoretical noise lower bound ($\approx 6.38$) while running in **$< 0.25$ ms per district**.
- Built an in-memory **ResidualTracker** computing chronological residuals, rolling bias, empirical variance, and standardized Z-scores to feed Phase 4 without polluting the baseline forecast.
- Added four REST API endpoints in FastAPI with full Pydantic v2 validation.
- Connected the React frontend service layer with live API support and offline mock fallback.
- Added 30 new unit/integration tests in `backend/tests/test_forecasting.py`. All 49 tests in the repository pass cleanly (19 Phase 1 + 30 Phase 2).

---

## 2. Files Created

1. `backend/app/forecasting/schemas.py`: Pydantic v2 schemas (`DemandHistoryPoint`, `FutureForecastPoint`, `DistrictForecastResult`, `ForecastRequest`, `ForecastResponse`, `ValidationMetricReport`).
2. `backend/app/forecasting/metrics.py`: Official competition metric ($U_{\text{forecast}}$) and diagnostics (MAE, RMSE, MAPE).
3. `backend/app/forecasting/models/base.py`: Abstract base class `BaseForecaster` with `fit()`, `predict()`, and `predict_with_uncertainty()`.
4. `backend/app/forecasting/models/harmonic_regression.py`: Primary OLS Harmonic Regression model with closed-form parameter estimation and leverage-adjusted prediction intervals.
5. `backend/app/forecasting/models/seasonal_naive.py`: Seasonal Naive benchmark ($t-12$).
6. `backend/app/forecasting/models/moving_average.py`: Moving Average / Local Level baseline.
7. `backend/app/forecasting/models/exponential_smoothing.py`: Holt / Holt-Winters exponential smoothing wrapper with fast heuristic initialization.
8. `backend/app/forecasting/models/ensemble.py`: Inverse-variance weighted ensemble forecaster.
9. `backend/app/forecasting/models/__init__.py`: Central model registry and factory functions (`get_model`, `list_models`).
10. `backend/app/forecasting/residuals.py`: `ResidualTracker` for chronological residuals, rolling variance, and Z-scores.
11. `backend/app/forecasting/validator.py`: `RollingOriginValidator` implementing strict leakage-free time-series cross-validation.
12. `backend/app/forecasting/engine.py`: `ForecastingEngine` orchestrating all 12 districts, sequential stepping, and risk classification.
13. `backend/tests/test_forecasting.py`: 30 automated unit and integration tests.
14. `phase2_implementation_report.md`: Complete implementation report.
15. `phase2_workflow.md`: Complete execution workflow log.

---

## 3. Files Modified

1. `backend/app/forecasting/__init__.py`: Exported all public classes, models, and metric utilities.
2. `backend/app/forecasting/forecaster.py`: Re-exported `ForecastingEngine` and key classes for backward compatibility.
3. `backend/app/main.py`: Replaced placeholder routes with real forecasting endpoints (`GET /api/forecasts`, `GET /api/forecasts/{district_id}`, `POST /api/forecast/predict`, `POST /api/forecast/validate`).
4. `frontend/src/services/forecastService.ts`: Connected service calls to `GET /api/forecasts` when `VITE_API_URL` is set, preserving mock fallback.

---

## 4. Files Protected

The following files were preserved and remained strictly untouched:
- `backend/app/generator/generator.py` (Phase 1 core)
- `backend/app/generator/__init__.py` (Phase 1 exports)
- `backend/tests/test_generator.py` (19 Phase 1 unit tests — all 19 remain passing)
- `frontend/src/services/mockData.ts` (deterministic mock data fallback)
- `frontend/src/components/ForecastChart.tsx`
- `frontend/src/components/ResidualChart.tsx`
- `frontend/src/pages/Dashboard.tsx`, `Allocation.tsx`, `SurgeMonitor.tsx`, `Simulation.tsx`

---

## 5. Forecasting Models Implemented

| Model | Implementation | Mathematical Basis | Complexity |
|---|---|---|---|
| **Harmonic Regression** | `HarmonicRegressionForecaster` | $\beta_0 + \beta_1 t + \beta_2 \sin\left(\frac{2\pi t}{12}\right) + \beta_3 \cos\left(\frac{2\pi t}{12}\right)$ | Closed-form OLS ($O(N)$) |
| **Seasonal Naive** | `SeasonalNaiveForecaster` | $\hat{y}_t = y_{t-12}$ | $O(1)$ indexing |
| **Moving Average** | `MovingAverageForecaster` | $\hat{y}_t = \frac{1}{k}\sum_{i=1}^k y_{t-i}$ | $O(k)$ averaging |
| **Exponential Smoothing** | `ExponentialSmoothingForecaster` | Additive trend & seasonal smoothing | Numerical optimization |
| **Ensemble** | `EnsembleForecaster` | $\sum_m w_m \hat{y}_m$, $w_m \propto 1/\text{MSE}_m$ | Convex combination |

---

## 6. Primary Model

**Selected Model:** `Harmonic Regression (Seasonal + Trend OLS)`

**Mathematical Justification:**
The HC-05 generator produces demand via:
$$\mu(d,t) = b_d + a_d \sin\left(\frac{2\pi t}{12} + \frac{d\pi}{6}\right) + g_d t$$
By the angle addition theorem:
$$\sin\left(\frac{2\pi t}{12} + \frac{d\pi}{6}\right) = \cos\left(\frac{d\pi}{6}\right) \sin\left(\frac{2\pi t}{12}\right) + \sin\left(\frac{d\pi}{6}\right) \cos\left(\frac{2\pi t}{12}\right)$$
This formulation is strictly linear in four coefficients. Because the noise is additive i.i.d. Gaussian $\varepsilon \sim \mathcal{N}(0, 8^2)$, the Gauss-Markov theorem proves that **OLS is the Minimum Variance Linear Unbiased Estimator (MVLUE)**.

---

## 7. Model Selection Results

The 5 implemented models were evaluated on the exact same rolling-origin cross-validation protocol over historical data ($T \in [24..35]$, 144 out-of-sample evaluations):

| Rank | Model Name | $U_{\text{forecast}}$ | MAE | RMSE | MAPE | Total Runtime (144 fits) |
|---|---|---|---|---|---|---|
| **1** | **Harmonic Regression** | **0.9400** | **7.819** | **9.550** | **6.69%** | **32.7 ms** |
| 2 | Ensemble | 0.9355 | 8.396 | 10.744 | 6.95% | 41.4 ms |
| 3 | Exponential Smoothing | 0.9274 | 9.451 | 11.586 | 7.94% | 8,471.6 ms |
| 4 | Seasonal Naive | 0.8982 | 13.257 | 16.555 | 10.52% | 5.2 ms |
| 5 | Moving Average ($k=3$) | 0.8749 | 16.292 | 19.883 | 13.25% | 27.9 ms |

---

## 8. Rolling Validation Results

- **Validation Protocol:** Rolling origins $T = 24, 25, \dots, 35$ (12 evaluation origins per district $\times$ 12 districts = 144 evaluations).
- **Training Window:** At origin $T$, the training window is strictly $t \in [0, T-1]$ ($N \in [24, 35]$).
- **Target:** Out-of-sample point at $t = T$.
- **Information Constraint:** Zero future observations, zero hidden evaluator seeds, and zero surge parameters were accessible to the model.

---

## 9. $U_{\text{forecast}}$ Results

The competition metric formula:
$$U_{\text{forecast}} = \max\left(0, 1 - \frac{\sum_{d=0}^{11}\sum_{t=24}^{35} |y_{d,t} - \hat{y}_{d,t}|}{\sum_{d=0}^{11}\sum_{t=24}^{35} \max(y_{d,t}, 1)}\right)$$

- **Harmonic Regression Utility:** **$0.9400$** (94.00%)
- **Seasonal Naive Benchmark Utility:** **$0.8982$** (89.82%)
- **Absolute Improvement:** **$+4.18$ percentage points** ($+0.0418$)

---

## 10. MAE / RMSE Results

- **Harmonic Regression:** $\text{MAE} = 7.819$, $\text{RMSE} = 9.550$
- **Theoretical Lower Bound:** For noise $\varepsilon \sim \mathcal{N}(0, 8^2)$, the expected absolute error is:
  $$\mathbb{E}[|\varepsilon|] = 8.0 \times \sqrt{\frac{2}{\pi}} \approx 6.383$$
- Harmonic Regression's MAE of 7.819 captures virtually all predictable structural signal, with residual error dominated by irreducible noise.

---

## 11. Runtime Results

- **Harmonic Regression Fit Time:** $\approx 0.22$ ms per fit.
- **12-District Horizon Forecast:** $< 5.0$ ms total.
- **Full Rolling Validation (144 fits):** $32.7$ ms total.
- **Comparison:** Exponential smoothing required $8,471.6$ ms ($> 250\times$ slower) due to iterative optimization.

---

## 12. Residual Tracking

Implemented in `backend/app/forecasting/residuals.py` via `ResidualTracker`:
- Records `(district_id, month, forecast, actual, residual, absolute_error, z_score)`.
- Computes rolling mean bias over arbitrary windows.
- Computes unbiased sample variance: $s^2 = \frac{1}{N-1}\sum (e_i - \bar{e})^2$.
- Computes standardized Z-score: $Z_t = \frac{e_t}{\max(1.0, s)}$.
- Implements `is_anomaly(district_id, threshold=2.0)` to flag potential surges for Phase 4.

---

## 13. Uncertainty Implementation

- **Unbiased Residual Standard Deviation:**
  $$s = \sqrt{\frac{1}{N - 4}\sum_{i=1}^N (y_i - \hat{y}_i)^2}$$
- **Analytical Prediction Intervals ($1 - \alpha = 90\%$):**
  $$\hat{y}_h \pm t_{0.95, N-4} \cdot s \sqrt{1 + \mathbf{x}_h (\mathbf{X}^T \mathbf{X})^{-1} \mathbf{x}_h^T}$$
  accounting for both random Gaussian variance and parameter estimation uncertainty via the leverage factor $\mathbf{x}_h (\mathbf{X}^T \mathbf{X})^{-1} \mathbf{x}_h^T$.
- **Enforced Invariants:**
  - $\text{lower} \le \text{forecast} \le \text{upper}$
  - $\text{lower} \ge 0$ (clamped)
  - All forecasts and bounds are integer-valued.

---

## 14. API Endpoints

The following REST endpoints were implemented in `backend/app/main.py`:

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Healthcheck and list of available models |
| `GET` | `/api/forecasts` | Returns latest 12-district forecasts conforming to frontend `DistrictForecast[]` |
| `GET` | `/api/forecasts/{district_id}` | Detailed forecast, trend, seasonality, and intervals for a district |
| `POST` | `/api/forecast/predict` | Multi-district forecasting given parameters or custom demand history |
| `POST` | `/api/forecast/validate` | Runs rolling-origin cross-validation and returns comparison reports |

---

## 15. Frontend Integration

- **Service File:** `frontend/src/services/forecastService.ts` updated.
- **Functionality:** Calls `/api/forecasts` via `apiGet` when `VITE_API_URL` is configured.
- **Fallback:** Gracefully catches network errors or unconfigured URL and falls back to `mockData.ts`.
- **Production Build:** Verified with `npm run build` in `frontend/`. Built in 52.19s with 0 TypeScript or bundling errors.

---

## 16. Database Decision

**Decision: NO DATABASE USED.**
- The HC-05 competition scoring is 100% code-executed in memory.
- Demand forecasting is a pure deterministic functional mapping from observed historical demand to future estimates and uncertainty intervals.
- Adding a relational database (Postgres/SQLite) introduces deployment fragility, migration drift, and disk I/O latency with zero competition utility benefit.
- All state serialization is handled cleanly via Pydantic v2.

---

## 17. Test Results

**Full Test Suite Result:** `49 passed in 8.65s`
- `backend/tests/test_forecasting.py`: 30 passed
- `backend/tests/test_generator.py`: 19 passed
- Total: **49 passing tests** (exceeding target of 44+).

---

## 18. Phase 1 Regression Test Results

All 19 Phase 1 unit tests were re-executed:
```text
backend/tests/test_generator.py::test_1_num_districts PASSED
backend/tests/test_generator.py::test_2_district_ids PASSED
backend/tests/test_generator.py::test_3_total_months PASSED
backend/tests/test_generator.py::test_4_historical_period PASSED
backend/tests/test_generator.py::test_5_future_period PASSED
backend/tests/test_generator.py::test_6_demand_values_non_negative_integers PASSED
backend/tests/test_generator.py::test_7_b_d_range PASSED
backend/tests/test_generator.py::test_8_a_d_range PASSED
backend/tests/test_generator.py::test_9_g_d_range PASSED
backend/tests/test_generator.py::test_10_capacity_follows_formula PASSED
backend/tests/test_generator.py::test_11_reserve_is_exactly_60 PASSED
backend/tests/test_generator.py::test_12_and_13_development_surge_exact_and_isolated PASSED
backend/tests/test_generator.py::test_14_deterministic_same_seed PASSED
backend/tests/test_generator.py::test_15_different_seeds_produce_different_scenarios PASSED
backend/tests/test_generator.py::test_16_matrix_dimensions PASSED
backend/tests/test_generator.py::test_17_serialization PASSED
backend/tests/test_generator.py::test_18_custom_surge_configuration PASSED
backend/tests/test_generator.py::test_19_dataframe_export PASSED
backend/tests/test_generator.py::test_20_demand_equation_and_noise_exactness PASSED
```
Zero regressions detected.

---

## 19. Sequential Constraint Verification

Verified in `test_26_sequential_decision_cycle`:
- Month 36 forecasted using history $0..35$. Month 36 actual revealed.
- Month 37 forecasted using history $0..36$. Month 37 actual revealed.
- Month 38 forecasted using history $0..37$. Month 38 actual revealed.
- Month 39 forecasted using history $0..38$. Month 39 actual revealed.
- Month 40 forecasted using history $0..39$. Month 40 actual revealed.
- Month 41 forecasted using history $0..40$. Month 41 actual revealed.
- No future actual demand was ever accessible before generating that month's prediction.

---

## 20. Development Scenario Verification

- Tested against `generate_development_scenario(seed=DEFAULT_SEED)` where $D2$ and $D9$ experience a $+35$ surge during months $38, 39, 40$.
- The forecasting pipeline received zero privileged knowledge regarding surge districts or timing.
- The forecaster predicted baseline demand, and the `ResidualTracker` accurately logged positive surge residuals ($Z \approx +3.8$ for $D2$ at $t=38$).

---

## 21. Reproducibility Verification

- Verified in `test_22_reproducibility_determinism`:
  - Calling the engine twice with identical historical demand matrices produces **bitwise identical** point forecasts, lower bounds, upper bounds, and parameter estimates.
- Zero unseeded random number generation is used anywhere in the forecasting subsystem.

---

## 22. Known Limitations

- Harmonic Regression assumes a single fundamental frequency (12-month period). If a synthetic scenario introduces secondary harmonics (e.g. 6-month bi-annual cycles), additional Fourier terms $[\sin(4\pi t/12), \cos(4\pi t/12)]$ would be required.
- Extreme nonlinear trend shifts (e.g. exponential growth) are approximated by a linear tangent over the 36-month window.

---

## 23. Issues Encountered and Fixes

1. **Slow Statsmodels Optimization:**
   - *Issue:* Statsmodels `ExponentialSmoothing` with default BFGS optimizer took $> 35$ seconds for rolling validation.
   - *Fix:* Configured `initialization_method="heuristic"` and seasonal component check, reducing runtime and preventing timeouts.
2. **Degrees of Freedom Safety:**
   - *Issue:* Small historical samples ($N < 4$) cannot invert the 4-parameter design matrix.
   - *Fix:* Added explicit input validation raising a clean `ValueError` when $N < 4$, with tests verifying this boundary.

---

## 24. Remaining Work for Phase 3

Phase 2 provides all prerequisites for Phase 3 (Resource Allocation Engine):
- Point forecasts $\hat{y}_d$ per district.
- Calibrated residual standard deviations $s_d$.
- Nominal capacities $c_d = \text{round}(0.90 \cdot b_d)$.
- Phase 3 will consume these outputs to compute shortage probabilities $\mathbb{P}(Y_d > c_d + a_d)$ and optimize the allocation of the 60-unit emergency reserve.

---

## 25. Final Status

**Phase 2 Implementation: 100% COMPLETE.**  
All tests passing, all constraints satisfied, and ready for Phase 3.
