"""
Optimization Engine for Emergency Reserve Allocation — HC-05 SurgeShield.

Implements discrete fair marginal-benefit knapsack optimization and MILP formulation
to allocate 60 integer reserve units while balancing aggregate unmet demand reduction
and worst-district service protection.
"""

from __future__ import annotations

import math
from typing import Sequence
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

from app.allocation.risk import expected_unmet_demand, marginal_benefit


class GreedyMarginalOptimizer:
    """
    Fairness-Weighted Marginal Benefit Knapsack Optimizer.
    
    Properties:
    - Exactly satisfies budget constraint: sum(x_d) <= budget (typically 60).
    - Guarantees integer allocations: x_d in Z >= 0.
    - Balances aggregate unmet demand reduction with worst-district equity.
    - Incorporates online surge adaptation signals.
    - Deterministic and sub-millisecond execution.
    """

    def __init__(
        self,
        fairness_weight: float = 1.5,
        floor_service_ratio: float = 0.85,
        max_fairness_units: int = 24,
    ):
        self.fairness_weight = fairness_weight
        self.floor_service_ratio = floor_service_ratio
        self.max_fairness_units = max_fairness_units

    def allocate(
        self,
        district_ids: Sequence[str],
        forecasts: dict[str, int | float],
        capacities: dict[str, int],
        sigmas: dict[str, float],
        reserve_budget: int = 60,
        surge_signals: dict[str, float] | None = None,
        policy: str = "Surge Adaptive",
    ) -> dict[str, int]:
        """
        Computes integer allocation vector x_d for each district.
        """
        allocations: dict[str, int] = {d: 0 for d in district_ids}
        signals = surge_signals or {}

        if reserve_budget <= 0 or not district_ids:
            return allocations

        # Specialized policy branches
        if policy == "Equal Split":
            base = reserve_budget // len(district_ids)
            rem = reserve_budget % len(district_ids)
            for i, d in enumerate(district_ids):
                allocations[d] = base + (1 if i < rem else 0)
            return allocations

        if policy == "Forecast Only":
            # Pure deficit proportional integer allocation (Hamilton-Hare method)
            gaps = {d: max(0.0, float(forecasts[d] - capacities[d])) for d in district_ids}
            total_gap = sum(gaps.values())
            if total_gap <= 0.0:
                # No deficits, distribute evenly
                base = reserve_budget // len(district_ids)
                rem = reserve_budget % len(district_ids)
                for i, d in enumerate(district_ids):
                    allocations[d] = base + (1 if i < rem else 0)
                return allocations

            exact_shares = {d: (gaps[d] / total_gap) * reserve_budget for d in district_ids}
            floored = {d: int(math.floor(exact_shares[d])) for d in district_ids}
            remainder = reserve_budget - sum(floored.values())
            # Distribute remainder by highest fractional parts
            remainders = sorted(
                district_ids,
                key=lambda d: (exact_shares[d] - floored[d], gaps[d]),
                reverse=True,
            )
            for d in remainders[:remainder]:
                floored[d] += 1
            return floored

        # For Risk Based, Fairness Aware, and Surge Adaptive:
        # Determine weighting parameters
        gamma = self.fairness_weight if policy in ("Fairness Aware", "Surge Adaptive") else 0.0
        surge_scale = 1.0 if policy == "Surge Adaptive" else 0.0
        units_allocated = 0

        # Stage 1: Fairness Floor Protection (for Fairness Aware and Surge Adaptive)
        if policy in ("Fairness Aware", "Surge Adaptive") and self.floor_service_ratio > 0.0:
            # Sort districts by initial projected service ratio
            def initial_ratio(d: str) -> float:
                fc = max(1.0, float(forecasts[d]))
                u = expected_unmet_demand(fc, capacities[d], 0.0, sigmas.get(d, 8.0))
                return 1.0 - (u / fc)

            vulnerable = sorted(district_ids, key=initial_ratio)
            for d in vulnerable:
                fc = max(1.0, float(forecasts[d]))
                sig = sigmas.get(d, 8.0)
                # Assign units while ratio < floor and budget permits
                while units_allocated < self.max_fairness_units and units_allocated < reserve_budget:
                    cur_x = allocations[d]
                    cur_u = expected_unmet_demand(fc, capacities[d], cur_x, sig)
                    cur_ratio = 1.0 - (cur_u / fc)
                    if cur_ratio >= self.floor_service_ratio:
                        break
                    allocations[d] += 1
                    units_allocated += 1

        # Stage 2: Marginal Knapsack Step-by-Step Allocation
        remaining_units = reserve_budget - sum(allocations.values())

        for _ in range(remaining_units):
            best_district = None
            best_score = -1.0

            for d in district_ids:
                cur_x = allocations[d]
                fc = float(forecasts[d])
                cap = capacities[d]
                sig = sigmas.get(d, 8.0)
                mb = marginal_benefit(fc, cap, cur_x, sig)

                if mb <= 1e-6:
                    score = 1e-9
                else:
                    # Current service ratio
                    eff_cap = cap + cur_x
                    deficit_ratio = max(0.0, (fc - eff_cap) / max(1.0, fc))
                    # Fairness multiplier penalizes low service ratio
                    fairness_mult = 1.0 + gamma * (deficit_ratio ** 1.5)
                    # Surge signal multiplier adapts if previous surge anomaly was detected
                    s_sig = signals.get(d, 0.0)
                    surge_mult = 1.0 + (0.8 * s_sig * surge_scale)

                    score = mb * fairness_mult * surge_mult

                if score > best_score:
                    best_score = score
                    best_district = d

            if best_district is not None:
                allocations[best_district] += 1
            else:
                # Fallback: allocate to first district if all scores identical
                allocations[district_ids[0]] += 1

        return allocations


class MILPAllocator:
    """
    Mixed-Integer Linear Programming (MILP) Allocator using scipy.optimize.milp.
    Piecewise linear approximation of convex expected unmet demand curves.
    """

    def allocate(
        self,
        district_ids: Sequence[str],
        forecasts: dict[str, int | float],
        capacities: dict[str, int],
        sigmas: dict[str, float],
        reserve_budget: int = 60,
    ) -> dict[str, int]:
        """
        Solves integer allocation via scipy.optimize.milp.
        Uses discrete marginal slopes as piecewise linear upper bounding planes.
        """
        D = len(district_ids)
        K = 25  # Max reserve units considered per district for piecewise planes

        # Precompute discrete marginal benefits MB_d(k) for k = 0..K-1
        # E[u_d(x_d)] = E[u_d(0)] - sum_{k=0}^{x_d-1} MB_d(k)
        # Decision variable: delta_{d,k} in [0, 1], with x_d = sum_k delta_{d,k}
        num_vars = D * K
        c = np.zeros(num_vars)

        for i, d in enumerate(district_ids):
            fc = float(forecasts[d])
            cap = capacities[d]
            sig = sigmas.get(d, 8.0)
            for k in range(K):
                mb = marginal_benefit(fc, cap, k, sig)
                var_idx = i * K + k
                # We want to maximize total MB sum -> minimize -MB
                c[var_idx] = -mb

        # Constraint: sum_{d, k} delta_{d,k} <= reserve_budget
        A_budget = np.ones((1, num_vars))
        constraints = LinearConstraint(A_budget, lb=0, ub=reserve_budget)

        # Integrality: all delta_{d,k} in {0, 1}
        integrality = np.ones(num_vars)
        bounds = Bounds(lb=np.zeros(num_vars), ub=np.ones(num_vars))

        res = milp(c=c, integrality=integrality, bounds=bounds, constraints=constraints)

        allocations: dict[str, int] = {d: 0 for d in district_ids}
        if res.success:
            sol = np.round(res.x).astype(int)
            for i, d in enumerate(district_ids):
                d_units = int(np.sum(sol[i * K : (i + 1) * K]))
                allocations[d] = d_units
        else:
            # Fallback to greedy if solver fails
            fallback = GreedyMarginalOptimizer()
            return fallback.allocate(district_ids, forecasts, capacities, sigmas, reserve_budget)

        return allocations
