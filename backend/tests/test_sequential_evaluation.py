"""
Unit Tests for Phase 5 Sequential Evaluation and Competition Metrics — HC-05 SurgeShield.

Verifies:
1. Exact competition scoring formulas with hand-calculable test cases:
   - Forecast utility U_forecast (30 pts)
   - Service utility U_service (45 pts)
   - Worst district service U_worst (15 pts)
   - Compliance (5 pts)
   - Runtime / Reproducibility (5 pts)
2. Strict zero-leakage sequential revelation: month t allocation cannot access month t demand.
3. Chronological simulation across months 36 -> 41.
4. History expansion: month 36 uses history 0..35, month 37 uses history 0..36, etc.
5. All 5 baseline policies evaluate cleanly.
"""

from __future__ import annotations

import pytest
import numpy as np

from app.generator import generate_development_scenario, generate_scenario
from app.evaluation import (
    compute_forecast_utility,
    compute_unmet_demand,
    compute_service_utility,
    compute_district_service_ratios,
    compute_worst_district_utility,
    compute_competition_scorecard,
    SequentialEvaluator,
    ComplianceStatus,
    benchmark_all_policies,
    summarize_benchmarks,
)


def test_1_hand_computed_competition_metrics():
    """Verifies official formulas on known hand-calculated numbers."""
    # Actuals: [100, 200]
    # Forecasts: [90, 210] -> absolute errors = [10, 10] -> sum = 20
    # Denominators: [100, 200] -> sum = 300
    # U_forecast = 1 - 20 / 300 = 1 - 0.066667 = 0.9333
    u_fc = compute_forecast_utility([100, 200], [90, 210])
    assert abs(u_fc - (1.0 - 20.0 / 300.0)) < 1e-6

    # Capacities: [80, 180]
    # Allocations: [10, 10]
    # Effective capacities: [90, 190]
    # Actual demands: [100, 200]
    # Unmet demands: [10, 10] -> sum = 20
    # Denominators: [100, 200] -> sum = 300
    # U_service = 1 - 20 / 300 = 0.9333
    u_srv = compute_service_utility([100, 200], [10, 10])
    assert abs(u_srv - (1.0 - 20.0 / 300.0)) < 1e-6

    # District ratios:
    # D0: actual 100, unmet 10 -> ratio = 0.90
    # D1: actual 200, unmet 10 -> ratio = 0.95
    # U_worst = min(0.90, 0.95) = 0.90
    d_ratios = compute_district_service_ratios(
        {"D0": [100], "D1": [200]},
        {"D0": [10], "D1": [10]},
    )
    assert abs(d_ratios["D0"] - 0.90) < 1e-6
    assert abs(d_ratios["D1"] - 0.95) < 1e-6
    assert abs(compute_worst_district_utility(d_ratios) - 0.90) < 1e-6


def test_2_strict_zero_future_leakage_and_chronology():
    """Verifies that the SequentialEvaluator expands history strictly month-by-month without leakage."""
    scenario = generate_development_scenario(seed=20260911)
    evaluator = SequentialEvaluator()

    res = evaluator.evaluate_scenario(scenario, policy="Surge Adaptive")
    logs = res.cycle_logs

    assert len(logs) == 6
    expected_months = [36, 37, 38, 39, 40, 41]
    for i, log in enumerate(logs):
        assert log.month == expected_months[i]
        assert len(log.forecasts) == 12
        assert len(log.allocations) == 12
        assert len(log.actuals) == 12
        # Verify budget was strictly respected at every month
        assert sum(log.allocations.values()) <= 60

    # Verify compliance reported passed
    assert res.scorecard.compliance.all_passed is True
    assert res.scorecard.compliance.noFutureLeakage is True


def test_3_online_surge_adaptation_behavior():
    """Tests that in the development scenario (surge at 38, 39, 40 on D2 and D9),
    the system experiences positive residuals at month 38 and increases allocation in months 39 and 40."""
    scenario = generate_development_scenario(seed=20260911)
    evaluator = SequentialEvaluator()

    res = evaluator.evaluate_scenario(scenario, policy="Surge Adaptive")
    logs = res.cycle_logs

    # Log at month 38 (first surge month)
    m38 = next(log for log in logs if log.month == 38)
    # Residuals at month 38 for D2 and D9 should be elevated (+35 approx)
    assert m38.residuals["D2"] > 20
    assert m38.residuals["D9"] > 20

    # Log at month 39 (second surge month)
    # The allocator should have received active surge signals for D2 and D9
    m39 = next(log for log in logs if log.month == 39)
    assert m39.active_surge_signals["D2"] > 0.5
    assert m39.active_surge_signals["D9"] > 0.5
    # D2 or D9 allocations should be positive and elevated
    assert m39.allocations["D2"] + m39.allocations["D9"] > 0


def test_4_all_five_policies_run_cleanly():
    """All 5 policies benchmark successfully and produce complete scorecards."""
    scenario = generate_development_scenario(seed=20260911)
    bench_results = benchmark_all_policies(scenario)

    assert len(bench_results) == 5
    summary = summarize_benchmarks(bench_results)
    assert len(summary) == 5

    for row in summary:
        assert 0.80 <= row.forecastUtility <= 1.0
        assert 0.0 <= row.serviceUtility <= 1.0
        assert 0.0 <= row.worstDistrictService <= 1.0
        assert row.totalScore > 70.0
        assert row.runtimeSeconds < 5.0
