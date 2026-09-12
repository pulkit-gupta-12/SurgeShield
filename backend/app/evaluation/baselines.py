"""
Baseline Benchmark Subsystem — HC-05 SurgeShield.

Benchmarks candidate allocation policies against the proposed predictive optimization system:
1. Equal Split (60 / 12 = 5 units each)
2. Forecast Only (proportional to demand deficit)
3. Risk Based (proportional to shortage risk)
4. Fairness Aware (protects lowest service ratio)
5. Surge Adaptive (proposed policy with fairness knapsack & online surge adaptation)
"""

from __future__ import annotations

from typing import Sequence
import numpy as np
from pydantic import BaseModel

from app.generator import GeneratedScenario, generate_scenario, DEFAULT_SEED
from app.allocation.schemas import AllocationPolicy
from app.evaluation.sequential import SequentialEvaluator, SequentialEvaluationResult
from app.evaluation.metrics import CompetitionScorecard

POLICIES: list[AllocationPolicy] = [
    "Equal Split",
    "Forecast Only",
    "Risk Based",
    "Fairness Aware",
    "Surge Adaptive",
]


class PolicyBenchmarkComparison(BaseModel):
    policy: AllocationPolicy
    forecastUtility: float
    serviceUtility: float
    worstDistrictService: float
    totalUnmetDemand: int
    totalScore: float
    runtimeSeconds: float


class MultiSeedSummary(BaseModel):
    policy: AllocationPolicy
    seeds_evaluated: list[int]
    u_forecast_mean: float
    u_forecast_std: float
    u_service_mean: float
    u_service_std: float
    u_worst_mean: float
    u_worst_std: float
    total_unmet_mean: float
    total_unmet_std: float
    total_score_mean: float
    total_score_std: float
    runtime_mean: float


def benchmark_all_policies(
    scenario: GeneratedScenario,
    evaluator: SequentialEvaluator | None = None,
) -> dict[AllocationPolicy, SequentialEvaluationResult]:
    """
    Evaluates all 5 allocation policies sequentially on the provided scenario.
    """
    ev = evaluator or SequentialEvaluator()
    results: dict[AllocationPolicy, SequentialEvaluationResult] = {}

    for pol in POLICIES:
        res = ev.evaluate_scenario(scenario=scenario, policy=pol)
        results[pol] = res

    return results


def summarize_benchmarks(
    benchmark_results: dict[AllocationPolicy, SequentialEvaluationResult]
) -> list[PolicyBenchmarkComparison]:
    """
    Converts benchmark results into a clean tabular scorecard comparison.
    """
    rows = []
    for pol, res in benchmark_results.items():
        sc: CompetitionScorecard = res.scorecard
        rows.append(
            PolicyBenchmarkComparison(
                policy=pol,
                forecastUtility=sc.forecastUtility,
                serviceUtility=sc.demandServiceUtility,
                worstDistrictService=sc.worstDistrictService,
                totalUnmetDemand=sc.totalUnmetDemand,
                totalScore=sc.totalScore,
                runtimeSeconds=res.runtime_seconds,
            )
        )
    return sorted(rows, key=lambda r: r.totalScore, reverse=True)


def run_multi_seed_stress_test(
    seeds: Sequence[int],
    policies: Sequence[AllocationPolicy] = POLICIES,
) -> dict[AllocationPolicy, MultiSeedSummary]:
    """
    Runs full sequential simulations across multiple scenario seeds to establish statistical robustness.
    """
    evaluator = SequentialEvaluator()
    # policy -> list of metrics
    storage: dict[AllocationPolicy, dict[str, list[float]]] = {
        p: {
            "u_fc": [],
            "u_srv": [],
            "u_worst": [],
            "unmet": [],
            "score": [],
            "runtime": [],
        }
        for p in policies
    }

    for seed in seeds:
        scen = generate_scenario(seed=seed)
        for p in policies:
            res = evaluator.evaluate_scenario(scen, policy=p)
            sc = res.scorecard
            storage[p]["u_fc"].append(sc.forecastUtility)
            storage[p]["u_srv"].append(sc.demandServiceUtility)
            storage[p]["u_worst"].append(sc.worstDistrictService)
            storage[p]["unmet"].append(float(sc.totalUnmetDemand))
            storage[p]["score"].append(sc.totalScore)
            storage[p]["runtime"].append(res.runtime_seconds)

    summaries: dict[AllocationPolicy, MultiSeedSummary] = {}
    for p in policies:
        summaries[p] = MultiSeedSummary(
            policy=p,
            seeds_evaluated=list(seeds),
            u_forecast_mean=round(float(np.mean(storage[p]["u_fc"])), 4),
            u_forecast_std=round(float(np.std(storage[p]["u_fc"], ddof=1)), 4),
            u_service_mean=round(float(np.mean(storage[p]["u_srv"])), 4),
            u_service_std=round(float(np.std(storage[p]["u_srv"], ddof=1)), 4),
            u_worst_mean=round(float(np.mean(storage[p]["u_worst"])), 4),
            u_worst_std=round(float(np.std(storage[p]["u_worst"], ddof=1)), 4),
            total_unmet_mean=round(float(np.mean(storage[p]["unmet"])), 1),
            total_unmet_std=round(float(np.std(storage[p]["unmet"], ddof=1)), 1),
            total_score_mean=round(float(np.mean(storage[p]["score"])), 2),
            total_score_std=round(float(np.std(storage[p]["score"], ddof=1)), 2),
            runtime_mean=round(float(np.mean(storage[p]["runtime"])), 4),
        )

    return summaries
