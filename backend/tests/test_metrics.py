"""
Official Competition Metrics and Scorecard Verification — HC-05 SurgeShield.

Verifies:
1. Forecast utility: 30 * U_forecast clipped to [0, 1].
2. Demand-service utility: 45 * U_service clipped to [0, 1].
3. Worst-district service: 15 * U_worst = min_d(r_d).
4. Compliance: 5 points if reserve <= 60, integer allocations, zero leakage, reproducible.
5. Runtime: 5 points if runtime <= 5.0 seconds.
6. Edge case robustness: zero demand, perfect forecasts, total service failure.
"""

from __future__ import annotations

import pytest
import numpy as np
from app.evaluation.metrics import (
    compute_forecast_utility,
    compute_unmet_demand,
    compute_service_utility,
    compute_district_service_ratios,
    compute_worst_district_utility,
    compute_competition_scorecard,
    ComplianceStatus,
)


def test_1_perfect_scorecard_yields_100_points():
    """When forecasts and service are 100% perfect, total score must equal 100.0."""
    actuals = {"D0": [100, 100], "D1": [100, 100]}
    forecasts = {"D0": [100, 100], "D1": [100, 100]}
    allocations = {"D0": [10, 10], "D1": [10, 10]}
    capacities = {"D0": 90, "D1": 90}  # cap(90) + res(10) = 100 -> unmet = 0

    scorecard = compute_competition_scorecard(
        actuals_matrix=actuals,
        forecasts_matrix=forecasts,
        allocations_matrix=allocations,
        capacities=capacities,
        runtime_seconds=0.1,
    )
    assert scorecard.forecastUtility == 1.0
    assert scorecard.demandServiceUtility == 1.0
    assert scorecard.worstDistrictService == 1.0
    assert scorecard.compliance.all_passed is True
    assert scorecard.totalUnmetDemand == 0
    assert scorecard.totalScore == 100.0


def test_2_clipping_bounds_and_division_by_zero():
    """Extreme errors and zero demand should clip safely to [0, 1]."""
    # Extreme forecast error: actual 10, forecast 1000
    u_fc = compute_forecast_utility([10], [1000])
    assert u_fc == 0.0

    # Zero actuals handled gracefully
    u_zero = compute_forecast_utility([], [])
    assert u_zero == 1.0

    # Total unmet exceeds demand
    u_srv = compute_service_utility([50], [500])
    assert u_srv == 0.0


def test_3_compliance_failure_deducts_points():
    """Non-compliance forfeits the 5 compliance points."""
    actuals = {"D0": [100]}
    forecasts = {"D0": [100]}
    allocations = {"D0": [0]}
    capacities = {"D0": 100}

    bad_compliance = ComplianceStatus(
        reserveConstraint=False,
        integerAllocations=True,
        noFutureLeakage=True,
        reproducibleConfig=True,
    )
    scorecard = compute_competition_scorecard(
        actuals_matrix=actuals,
        forecasts_matrix=forecasts,
        allocations_matrix=allocations,
        capacities=capacities,
        compliance=bad_compliance,
        runtime_seconds=0.05,
    )
    # Perfect forecast(30) + perfect service(45) + perfect worst(15) + runtime(5) = 95
    assert scorecard.totalScore == 95.0
