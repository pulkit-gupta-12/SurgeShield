"""
Comprehensive Test Suite for Phase 2 Forecasting Engine — HC-05 SurgeShield.

Verifies:
1. Exact competition forecast utility formula: U_forecast = 1 - sum(|y - y_hat|) / sum(max(y, 1)) clipped to [0, 1].
2. Metric edge cases: perfect forecast (1.0), zero demand denominator safety, extreme errors clipping to 0.0.
3. Standard regression diagnostics: MAE, RMSE, MAPE.
4. Harmonic regression closed-form parameter recovery on clean mathematical signal.
5. Harmonic regression prediction shape and horizons.
6. Seasonal naive behavior and lag-12 indexing.
7. Moving average smoothing over window k.
8. Exponential smoothing stability and prediction bounds.
9. Ensemble inverse-variance weighting and predictions.
10. Non-negative integer forecast enforcement.
11. Calibrated uncertainty bounds: lower <= forecast <= upper.
12. Non-negative lower bound enforcement: lower >= 0.
13. Residual standard error estimation on Gaussian noise.
14. ResidualTracker chronological recording of month, forecast, actual, residual, and abs_error.
15. ResidualTracker rolling mean bias and variance calculation.
16. ResidualTracker standardized Z-score and anomaly detection.
17. RollingOriginValidator chronological ordering and window constraints (t=24..35).
18. Strict zero-leakage enforcement during rolling-origin evaluation.
19. Multi-district rolling validation matrix evaluation across all 12 districts.
20. Model ranking on rolling validation utility.
21. ForecastingEngine multi-district forecast generation.
22. Risk level classification (Critical, High, Medium, Low) based on capacity gap.
23. Reproducibility: bitwise identical forecasts given identical inputs.
24. Edge case: flat/constant demand series.
25. Edge case: near-zero demand series.
26. Edge case: error raised on insufficient history (< 4 observations).
27. Phase 1 integration: seamless consumption of GeneratedScenario historical matrix.
28. Sequential 6-month simulation test (months 36..41 without future leakage).
29. FastAPI endpoints integration (/api/health, /api/forecasts, /api/forecast/predict, /api/forecast/validate).
"""

from __future__ import annotations

import math
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.generator import (
    generate_scenario,
    generate_base_scenario,
    generate_development_scenario,
    DEFAULT_SEED,
)
from app.forecasting import (
    compute_forecast_utility,
    compute_mae,
    compute_rmse,
    compute_mape,
    evaluate_predictions,
    BaseForecaster,
    HarmonicRegressionForecaster,
    SeasonalNaiveForecaster,
    MovingAverageForecaster,
    ExponentialSmoothingForecaster,
    EnsembleForecaster,
    get_model,
    list_models,
    ResidualTracker,
    ResidualRecord,
    RollingOriginValidator,
    ForecastingEngine,
    classify_risk,
    ForecastRequest,
)
from app.main import app


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def clean_synthetic_series() -> tuple[np.ndarray, float, float, float]:
    """
    Noiseless HC-05 signal:
        b = 100, g = 0.5, a = 20, d = 0 (phase = 0)
        y(t) = 100 + 0.5*t + 20*sin(2πt/12)
    """
    t = np.arange(36, dtype=float)
    y = 100.0 + 0.5 * t + 20.0 * np.sin(2.0 * math.pi * t / 12.0)
    return y, 100.0, 0.5, 20.0


@pytest.fixture
def dev_scenario():
    """Official Phase 1 development scenario."""
    return generate_development_scenario(seed=DEFAULT_SEED)


@pytest.fixture
def client():
    """FastAPI TestClient."""
    return TestClient(app)


# ── 1. Competition Metric Tests ───────────────────────────────────────────────

def test_1_competition_metric_formula_and_perfect_forecast():
    """Verify U_forecast = 1.0 when forecasts exactly match actuals."""
    y = np.array([100, 120, 95, 110, 105])
    u = compute_forecast_utility(y, y)
    assert u == 1.0


def test_2_competition_metric_clipping_bounds():
    """Verify U_forecast is strictly clipped to [0.0, 1.0]."""
    y_true = np.array([10, 10, 10])
    y_wild = np.array([1000, 1000, 1000])  # extreme over-forecast
    u = compute_forecast_utility(y_true, y_wild)
    assert u == 0.0

    # Under-forecast
    y_zero = np.array([0, 0, 0])
    u_zero = compute_forecast_utility(y_true, y_zero)
    assert 0.0 <= u_zero <= 1.0


def test_3_competition_metric_zero_actual_denominator_safety():
    """Verify denominator uses max(actual, 1) so division by zero is impossible."""
    y_true = np.array([0, 0, 0])
    y_pred = np.array([5, 5, 5])
    u = compute_forecast_utility(y_true, y_pred)
    assert isinstance(u, float)
    assert 0.0 <= u <= 1.0


def test_4_regression_diagnostic_metrics():
    """Verify MAE, RMSE, and MAPE calculations."""
    y_true = np.array([100, 110, 120])
    y_pred = np.array([102, 108, 125])
    metrics = evaluate_predictions(y_true, y_pred)
    assert pytest.approx(metrics["mae"], 0.01) == (2 + 2 + 5) / 3.0
    assert metrics["rmse"] > metrics["mae"]
    assert metrics["u_forecast"] > 0.90


# ── 2. Model Mathematical Correctness & Parameter Recovery ───────────────────

def test_5_harmonic_regression_parameter_recovery(clean_synthetic_series):
    """
    Harmonic regression should recover exact b, g, and amplitude on clean signal.
    """
    y, true_b, true_g, true_a = clean_synthetic_series
    model = HarmonicRegressionForecaster(period=12.0)
    model.fit(y)

    assert pytest.approx(model.baseline_, abs=0.01) == true_b
    assert pytest.approx(model.trend_, abs=0.01) == true_g
    assert pytest.approx(model.amplitude_, abs=0.01) == true_a


def test_6_harmonic_regression_prediction_shape_and_future():
    """Verify prediction produces non-negative integer arrays for arbitrary horizons."""
    model = HarmonicRegressionForecaster()
    y = np.linspace(80, 120, 36)
    model.fit(y)

    for h in [1, 3, 6, 12]:
        preds = model.predict(horizon=h)
        assert len(preds) == h
        assert preds.dtype in (np.int32, np.int64)
        assert np.all(preds >= 0)


def test_7_seasonal_naive_behavior():
    """Verify seasonal naive repeats t-12 values."""
    pattern = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120])
    y = np.tile(pattern, 3)  # 36 months
    model = SeasonalNaiveForecaster(period=12)
    model.fit(y)

    preds = model.predict(horizon=12)
    assert np.array_equal(preds, pattern)


def test_8_moving_average_behavior():
    """Verify moving average predicts the mean of the recent k window."""
    y = np.array([10, 20, 30, 40, 50, 60])
    model = MovingAverageForecaster(window=3)
    model.fit(y)

    # Last 3 are 40, 50, 60 -> mean 50
    preds = model.predict(horizon=4)
    assert np.all(preds == 50)


def test_9_exponential_smoothing_behavior():
    """Verify ExponentialSmoothingForecaster runs reliably and outputs valid predictions."""
    y = 100 + 10 * np.sin(2 * np.pi * np.arange(36) / 12)
    model = ExponentialSmoothingForecaster()
    model.fit(y)
    preds = model.predict(horizon=6)
    assert len(preds) == 6
    assert np.all(preds >= 0)


def test_10_ensemble_weighting_and_predictions():
    """Verify EnsembleForecaster combines sub-models with valid weights."""
    y = 100 + 0.4 * np.arange(36) + 15 * np.sin(2 * np.pi * np.arange(36) / 12)
    ens = EnsembleForecaster()
    ens.fit(y)

    assert len(ens.learned_weights_) == 2
    assert pytest.approx(sum(ens.learned_weights_), 0.001) == 1.0
    preds = ens.predict(horizon=6)
    assert len(preds) == 6
    assert np.all(preds >= 0)


# ── 3. Uncertainty & Prediction Interval Tests ─────────────────────────────────

def test_11_prediction_intervals_ordering():
    """Verify lower <= forecast <= upper for all horizon steps."""
    y = 100 + 0.5 * np.arange(36) + np.random.default_rng(42).normal(0, 8, 36)
    model = HarmonicRegressionForecaster()
    model.fit(y)

    point, lower, upper = model.predict_with_uncertainty(horizon=6, alpha=0.10)
    for h in range(6):
        assert lower[h] <= point[h] <= upper[h]


def test_12_prediction_intervals_non_negative_lower():
    """Verify lower bound is strictly non-negative (>= 0)."""
    # Low demand series where margin might otherwise go negative
    y = np.array([5, 4, 6, 5, 4, 7, 5, 4, 6, 5, 4, 6] * 2)
    model = HarmonicRegressionForecaster()
    model.fit(y)

    _, lower, _ = model.predict_with_uncertainty(horizon=6, alpha=0.01)
    assert np.all(lower >= 0)


def test_13_residual_std_estimation(dev_scenario):
    """Verify estimated residual standard deviation aligns with theoretical noise sigma=8.0."""
    hist = dev_scenario.get_historical_matrix()
    model = HarmonicRegressionForecaster()
    model.fit(hist[0])

    # True noise has std 8.0; estimated should be in [6.0, 11.0]
    assert 6.0 <= model.residual_std_ <= 11.0


# ── 4. Residual Tracking Tests ────────────────────────────────────────────────

def test_14_residual_tracker_recording():
    """Verify ResidualTracker correctly records events and calculates errors."""
    tracker = ResidualTracker(default_sigma=8.0)
    rec = tracker.record(district_id="D2", month=36, forecast=140, actual=150)

    assert rec.residual == 10
    assert rec.absolute_error == 10
    assert rec.month == 36
    assert len(tracker.get_records("D2")) == 1


def test_15_residual_tracker_rolling_bias_and_variance():
    """Verify rolling mean and variance calculations."""
    tracker = ResidualTracker()
    tracker.record("D0", 1, forecast=100, actual=105)  # res = +5
    tracker.record("D0", 2, forecast=100, actual=115)  # res = +15
    tracker.record("D0", 3, forecast=100, actual=110)  # res = +10

    mean_bias = tracker.get_recent_mean("D0", window=3)
    assert pytest.approx(mean_bias, 0.01) == 10.0
    var = tracker.get_variance("D0")
    assert var > 0.0


def test_16_residual_tracker_z_score_and_anomaly():
    """Verify Z-score computation and anomaly detection for large residual."""
    tracker = ResidualTracker(default_sigma=8.0)
    tracker.record("D2", 36, forecast=100, actual=102)
    tracker.record("D2", 37, forecast=100, actual=101)
    # Inject large surge residual (+35)
    rec_surge = tracker.record("D2", 38, forecast=100, actual=135)

    assert rec_surge.z_score >= 3.0
    assert tracker.is_anomaly("D2", threshold=2.0) is True


# ── 5. Leakage-Free Rolling Validation Tests ──────────────────────────────────

def test_17_rolling_validator_zero_future_leakage():
    """
    Explicitly test that the validator trains strictly on t < origin.
    """
    validator = RollingOriginValidator(min_train_window=24, max_train_window=35)
    y = np.arange(36, dtype=float)

    # Custom spy model to inspect the training slice size at each fit
    class LeakageDetector(BaseForecaster):
        def __init__(self):
            super().__init__()
            self.train_lens = []

        def fit(self, y_train, t=None):
            self.train_lens.append(len(y_train))
            self.is_fitted = True
            return self

        def predict(self, horizon=1):
            return np.array([self.train_lens[-1]], dtype=int)

    detector = LeakageDetector()
    acts, preds = validator.validate_single_series(y, model=detector)

    # For origins 24..35, there should be 12 evaluations
    assert len(acts) == 12
    assert len(preds) == 12
    # The training sizes must strictly equal the origin indices: 24, 25, ..., 35
    expected_train_lens = list(range(24, 36))
    assert preds.tolist() == expected_train_lens


def test_18_rolling_validation_matrix_across_all_12_districts(dev_scenario):
    """Verify rolling validation executes across all 12 districts producing 144 evaluations."""
    hist = dev_scenario.get_historical_matrix()  # (12, 36)
    validator = RollingOriginValidator(min_train_window=24, max_train_window=35)

    report = validator.validate_matrix(hist, model="harmonic_regression")
    assert report.num_evaluations == 12 * 12  # 144 points
    assert report.u_forecast >= 0.90
    assert report.mae <= 9.0
    assert len(report.per_district_mae) == 12
    assert len(report.per_district_utility) == 12


def test_19_model_ranking_on_rolling_validation(dev_scenario):
    """Verify Harmonic Regression beats Seasonal Naive on rolling validation."""
    hist = dev_scenario.get_historical_matrix()
    validator = RollingOriginValidator(min_train_window=24, max_train_window=35)

    reports = validator.compare_models(hist, models=["harmonic_regression", "seasonal_naive"])
    assert len(reports) == 2
    # First ranked model must have highest U_forecast
    assert reports[0].u_forecast >= reports[1].u_forecast
    assert reports[0].model_name == "harmonic_regression"


# ── 6. Forecasting Engine & Orchestration Tests ───────────────────────────────

def test_20_forecasting_engine_multi_district_forecast(dev_scenario):
    """Verify engine generates forecasts for all 12 districts with complete metadata."""
    engine = ForecastingEngine()
    hist = dev_scenario.get_historical_matrix()
    caps = dev_scenario.capacities

    res = engine.forecast_all_districts(
        historical_matrix=hist,
        capacities=caps,
        horizon=6,
        start_month=36,
    )

    assert len(res.districts) == 12
    for d_id in dev_scenario.districts:
        d_res = res.districts[d_id]
        assert d_res.district_id == d_id
        assert len(d_res.future) == 6
        assert len(d_res.history) == 36
        assert d_res.risk_level in ("Low", "Medium", "High", "Critical")


def test_21_risk_classification():
    """Verify risk classification boundaries."""
    assert classify_risk(forecast=140, capacity=100) == "Critical"  # gap 40 >= 30
    assert classify_risk(forecast=120, capacity=100) == "High"      # gap 20 >= 15
    assert classify_risk(forecast=108, capacity=100) == "Medium"    # gap 8 >= 5
    assert classify_risk(forecast=102, capacity=100) == "Low"       # gap 2 < 5


def test_22_reproducibility_determinism(dev_scenario):
    """Verify identical inputs produce identical forecasts."""
    engine1 = ForecastingEngine()
    engine2 = ForecastingEngine()
    hist = dev_scenario.get_historical_matrix()

    res1 = engine1.forecast_all_districts(hist, horizon=6)
    res2 = engine2.forecast_all_districts(hist, horizon=6)

    for d_id in dev_scenario.districts:
        f1 = [p.forecast for p in res1.districts[d_id].future]
        f2 = [p.forecast for p in res2.districts[d_id].future]
        assert f1 == f2


# ── 7. Edge Cases & Robustness Tests ─────────────────────────────────────────

def test_23_edge_case_constant_demand():
    """Verify stability on completely flat demand series."""
    y = np.full(36, 100.0)
    model = HarmonicRegressionForecaster()
    model.fit(y)
    preds = model.predict(horizon=6)
    assert np.all(preds == 100)


def test_24_edge_case_near_zero_demand():
    """Verify handling of near-zero demand without negative values."""
    y = np.array([0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0] * 3)
    model = HarmonicRegressionForecaster()
    model.fit(y)
    preds = model.predict(horizon=6)
    assert np.all(preds >= 0)


def test_25_edge_case_insufficient_history_raises_error():
    """Verify ValueError is raised when series has < 4 observations."""
    y = np.array([100, 105, 110])
    model = HarmonicRegressionForecaster()
    with pytest.raises(ValueError, match="at least 4 observations"):
        model.fit(y)


# ── 8. Sequential 6-Month Simulation Test ─────────────────────────────────────

def test_26_sequential_decision_cycle(dev_scenario):
    """
    Simulate the online sequential decision process for months 36..41.
    Verify that each month t forecast is made strictly before actual demand is observed.
    """
    engine = ForecastingEngine()
    hist_matrix = dev_scenario.get_historical_matrix()  # (12, 36)
    fut_matrix = dev_scenario.get_future_matrix()       # (12, 6)
    d_ids = dev_scenario.districts
    caps = dev_scenario.capacities

    # Current state of observed demand
    observed_history = {d_ids[i]: list(hist_matrix[i, :]) for i in range(12)}

    all_sequential_forecasts = {d_id: [] for d_id in d_ids}

    # Step sequentially through evaluation horizon t = 36..41
    for step_idx in range(6):
        curr_month = 36 + step_idx

        # 1. Previous month observed actuals (for t > 36)
        if step_idx > 0:
            prev_actuals = {d_ids[i]: int(fut_matrix[i, step_idx - 1]) for i in range(12)}
        else:
            prev_actuals = None

        # 2. Predict current month
        step_results = engine.step_sequential(
            current_month=curr_month,
            history_so_far=observed_history,
            capacities=caps,
            observed_previous_demand=prev_actuals,
        )

        for d_id in d_ids:
            all_sequential_forecasts[d_id].append(step_results[d_id].current_forecast)

        # 3. Reveal actual demand for curr_month and append to history for future steps
        for i, d_id in enumerate(d_ids):
            actual_curr = int(fut_matrix[i, step_idx])
            observed_history[d_id].append(actual_curr)

    # Verify 6 sequential forecasts were generated per district
    for d_id in d_ids:
        assert len(all_sequential_forecasts[d_id]) == 6

    # Verify residuals were properly recorded in the tracker
    records = engine.residual_tracker.get_records()
    assert len(records) == 12 * 5  # recorded for months 36..40 after revelation


# ── 9. FastAPI Endpoints Integration Tests ───────────────────────────────────

def test_27_api_health_endpoint(client):
    """Verify GET /api/health responds with status ok and available models."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "harmonic_regression" in data["models_available"]


def test_28_api_forecasts_endpoint(client):
    """Verify GET /api/forecasts returns all 12 districts in frontend format."""
    res = client.get("/api/forecasts")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 12

    first = data[0]
    assert "districtId" in first
    assert "currentForecast" in first
    assert "future" in first
    assert "history" in first
    assert len(first["future"]) == 6
    assert len(first["history"]) == 36


def test_29_api_forecast_predict_endpoint(client):
    """Verify POST /api/forecast/predict processes custom forecast requests."""
    payload = {
        "seed": 20260911,
        "horizon": 3,
        "start_month": 36,
        "model_type": "harmonic_regression",
    }
    res = client.post("/api/forecast/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["horizon"] == 3
    assert len(data["districts"]) == 12


def test_30_api_forecast_validate_endpoint(client):
    """Verify POST /api/forecast/validate runs rolling-origin validation."""
    res = client.post("/api/forecast/validate?models=harmonic_regression&models=seasonal_naive")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["model_name"] == "harmonic_regression"
    assert data[0]["u_forecast"] >= 0.90
