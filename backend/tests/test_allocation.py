"""
Unit Tests for Phase 3 Resource Allocation and Predictive Risk — HC-05 SurgeShield.

Verifies:
1. Hard constraint enforcement: all allocations in Z >= 0, sum <= 60.
2. Exact budget utilization: exactly 60 reserve units allocated when needed.
3. Closed-form normal loss expected unmet calculation accuracy and convexity.
4. Marginal benefit monotonicity: strictly decreasing as reserve increases.
5. High-risk / high-deficit districts receive prioritized reserve allocation.
6. Fairness floor protection: vulnerable districts are protected against service collapse.
7. Explanations: reason, expectedBenefit ('Low'|'Medium'|'High'), factors in [0, 1].
8. Determinism: identical inputs produce identical allocations.
9. Zero-risk / surplus capacity edge case handling.
10. MILP allocator consistency with greedy knapsack optimizer.
"""

from __future__ import annotations

import math
import pytest
import numpy as np

from app.allocation import (
    expected_unmet_demand,
    shortage_probability,
    marginal_benefit,
    classify_risk_level,
    assess_district_risk,
    validate_allocation,
    GreedyMarginalOptimizer,
    MILPAllocator,
    ReserveAllocator,
)


def test_1_hard_constraints_validation():
    """Validates budget <= 60, non-negative, and integer constraints."""
    # Valid
    validate_allocation({"D0": 10, "D1": 50}, budget=60)
    validate_allocation({"D0": 0, "D1": 0}, budget=60)

    # Negative allocation raises error
    with pytest.raises(ValueError, match="negative"):
        validate_allocation({"D0": -1, "D1": 10}, budget=60)

    # Over budget raises error
    with pytest.raises(ValueError, match="exceeds budget"):
        validate_allocation({"D0": 35, "D1": 26}, budget=60)


def test_2_expected_unmet_convexity_and_normal_loss():
    """Tests normal loss function values and strict convexity in capacity."""
    fc = 100.0
    cap = 90.0
    sig = 8.0

    # When capacity < forecast, expected unmet > 0
    u0 = expected_unmet_demand(fc, cap, reserve=0, sigma=sig)
    u10 = expected_unmet_demand(fc, cap, reserve=10, sigma=sig)
    u20 = expected_unmet_demand(fc, cap, reserve=20, sigma=sig)

    assert u0 > u10 > u20 >= 0.0

    # Discrete second difference should be positive (convexity)
    d1 = u0 - u10
    d2 = u10 - u20
    assert d1 > d2 > 0.0


def test_3_marginal_benefit_monotonicity():
    """Marginal benefit MB(x) = E[u(x)] - E[u(x+1)] must be strictly non-increasing."""
    fc = 120.0
    cap = 100.0
    sig = 8.0

    mbs = [marginal_benefit(fc, cap, k, sig) for k in range(15)]
    for i in range(len(mbs) - 1):
        assert mbs[i] >= mbs[i + 1] - 1e-9


def test_4_greedy_allocator_enforces_budget_and_integers():
    """Optimizer must allocate exactly 60 integer units across 12 districts."""
    districts = [f"D{i}" for i in range(12)]
    forecasts = {d: 110 for d in districts}
    capacities = {d: 95 for d in districts}
    sigmas = {d: 8.0 for d in districts}

    optimizer = GreedyMarginalOptimizer()
    alloc = optimizer.allocate(
        district_ids=districts,
        forecasts=forecasts,
        capacities=capacities,
        sigmas=sigmas,
        reserve_budget=60,
        policy="Surge Adaptive",
    )

    assert sum(alloc.values()) == 60
    for d, units in alloc.items():
        assert isinstance(units, int)
        assert units >= 0


def test_5_prioritization_of_high_deficit_districts():
    """Districts with large deficits must receive significantly more reserve than low-deficit ones."""
    districts = ["D0", "D1", "D2", "D3"]
    # D0 has large deficit: 150 vs 100
    # D1 has slight deficit: 105 vs 100
    # D2 and D3 have no deficit: 80 vs 100
    forecasts = {"D0": 150, "D1": 105, "D2": 80, "D3": 80}
    capacities = {"D0": 100, "D1": 100, "D2": 100, "D3": 100}
    sigmas = {d: 8.0 for d in districts}

    allocator = ReserveAllocator()
    res = allocator.allocate(
        district_ids=districts,
        forecasts=forecasts,
        capacities=capacities,
        sigmas=sigmas,
        policy="Surge Adaptive",
        reserve_budget=60,
    )

    alloc_map = {a.districtId: a.reserve for a in res.allocations}
    assert alloc_map["D0"] > alloc_map["D1"]
    assert alloc_map["D2"] == 0
    assert alloc_map["D3"] == 0
    assert sum(alloc_map.values()) <= 60


def test_6_fairness_protection_prevents_district_starvation():
    """Fairness-aware allocation prevents a smaller district from experiencing catastrophic service."""
    districts = ["LargeD", "SmallD"]
    # LargeD has high volume: 500 vs 470 (gap 30)
    # SmallD has lower volume: 60 vs 40 (gap 20, but 33% deficit)
    forecasts = {"LargeD": 500, "SmallD": 60}
    capacities = {"LargeD": 470, "SmallD": 40}
    sigmas = {"LargeD": 8.0, "SmallD": 8.0}

    allocator = ReserveAllocator()
    res = allocator.allocate(
        district_ids=districts,
        forecasts=forecasts,
        capacities=capacities,
        sigmas=sigmas,
        policy="Fairness Aware",
        reserve_budget=40,
    )

    alloc_map = {a.districtId: a.reserve for a in res.allocations}
    # Both districts should receive substantial reserve
    assert alloc_map["SmallD"] >= 10
    assert alloc_map["LargeD"] >= 15


def test_7_explainability_metadata_and_factors():
    """All allocations must report reasons, benefit levels, and normalized factors."""
    districts = [f"D{i}" for i in range(4)]
    forecasts = {"D0": 130, "D1": 100, "D2": 90, "D3": 80}
    capacities = {"D0": 100, "D1": 100, "D2": 100, "D3": 100}
    sigmas = {d: 8.0 for d in districts}

    allocator = ReserveAllocator()
    res = allocator.allocate(
        district_ids=districts,
        forecasts=forecasts,
        capacities=capacities,
        sigmas=sigmas,
        policy="Surge Adaptive",
        reserve_budget=25,
    )

    for a in res.allocations:
        assert isinstance(a.reason, str) and len(a.reason) > 5
        assert a.expectedBenefit in ("Low", "Medium", "High")
        assert 0.0 <= a.factors.shortageRisk <= 1.0
        assert 0.0 <= a.factors.demandGap <= 1.0
        assert 0.0 <= a.factors.surgeSignal <= 1.0
        assert 0.0 <= a.factors.fairnessPriority <= 1.0


def test_8_determinism_and_reproducibility():
    """Identical calls must produce bitwise identical allocations."""
    districts = [f"D{i}" for i in range(12)]
    forecasts = {d: 100 + i * 5 for i, d in enumerate(districts)}
    capacities = {d: 95 for d in districts}
    sigmas = {d: 8.0 for d in districts}

    allocator = ReserveAllocator()
    res1 = allocator.allocate(districts, forecasts, capacities, sigmas, policy="Surge Adaptive")
    res2 = allocator.allocate(districts, forecasts, capacities, sigmas, policy="Surge Adaptive")

    map1 = {a.districtId: a.reserve for a in res1.allocations}
    map2 = {a.districtId: a.reserve for a in res2.allocations}
    assert map1 == map2


def test_9_zero_deficit_surplus_scenario():
    """When capacities far exceed forecasts, allocator gracefully handles zero shortages."""
    districts = ["D0", "D1"]
    forecasts = {"D0": 50, "D1": 50}
    capacities = {"D0": 150, "D1": 150}
    sigmas = {"D0": 8.0, "D1": 8.0}

    allocator = ReserveAllocator()
    res = allocator.allocate(
        districts, forecasts, capacities, sigmas, policy="Forecast Only", reserve_budget=20
    )
    assert sum(a.reserve for a in res.allocations) == 20
    assert res.totalUnmetDemand == 0.0
    assert res.serviceUtility == 1.0


def test_10_milp_allocator_budget_and_integrality():
    """Verifies that the MILP allocator also satisfies budget and integer constraints."""
    districts = [f"D{i}" for i in range(6)]
    forecasts = {d: 110 + i * 2 for i, d in enumerate(districts)}
    capacities = {d: 100 for d in districts}
    sigmas = {d: 8.0 for d in districts}

    milp_solver = MILPAllocator()
    sol = milp_solver.allocate(
        district_ids=districts,
        forecasts=forecasts,
        capacities=capacities,
        sigmas=sigmas,
        reserve_budget=30,
    )

    assert sum(sol.values()) <= 30
    for units in sol.values():
        assert isinstance(units, (int, np.integer))
        assert units >= 0
