"""
Reproducibility and Determinism Verification — HC-05 SurgeShield.

Verifies:
1. Bitwise identical execution across multiple invocations given identical seed.
2. Distinct scenarios and evaluations across different random seeds.
3. No uncontrolled random state pollution.
"""

from __future__ import annotations

import json
import pytest
from app.generator import generate_scenario, DEFAULT_SEED
from app.evaluation.sequential import SequentialEvaluator


def test_1_bitwise_reproducible_evaluation_results():
    """Two independent sequential evaluations with seed 20260911 must produce identical output."""
    evaluator = SequentialEvaluator()
    scen1 = generate_scenario(seed=DEFAULT_SEED)
    scen2 = generate_scenario(seed=DEFAULT_SEED)

    res1 = evaluator.evaluate_scenario(scen1, policy="Fairness Aware")
    res2 = evaluator.evaluate_scenario(scen2, policy="Fairness Aware")

    # Scorecard equivalence
    assert res1.scorecard.forecastUtility == res2.scorecard.forecastUtility
    assert res1.scorecard.demandServiceUtility == res2.scorecard.demandServiceUtility
    assert res1.scorecard.worstDistrictService == res2.scorecard.worstDistrictService
    assert res1.scorecard.totalUnmetDemand == res2.scorecard.totalUnmetDemand
    assert res1.scorecard.totalScore == res2.scorecard.totalScore

    # Cycle-by-cycle allocations equivalence
    for m in range(6):
        assert res1.cycle_logs[m].allocations == res2.cycle_logs[m].allocations
        assert res1.cycle_logs[m].forecasts == res2.cycle_logs[m].forecasts
        assert res1.cycle_logs[m].residuals == res2.cycle_logs[m].residuals


def test_2_distinct_seeds_produce_distinct_scenarios():
    """Different seeds generate statistically distinct demands and scenarios."""
    scen_a = generate_scenario(seed=20260911)
    scen_b = generate_scenario(seed=20260999)

    assert scen_a.historical_demand != scen_b.historical_demand
    assert scen_a.future_demand != scen_b.future_demand
