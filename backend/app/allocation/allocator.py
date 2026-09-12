"""
Allocator Module — HC-05 SurgeShield.

Distributes 60 emergency medical reserve units across 12 districts under constraints:
- Total allocation <= 60
- Nonnegative integers only: x_d in Z >= 0
- Zero future leakage
- Explains rationale and computes diagnostic scores for every district
"""

from __future__ import annotations

import math
from typing import Sequence
import numpy as np

from app.allocation.schemas import (
    AllocationPolicy,
    AllocationResult,
    DistrictAllocation,
    AllocationFactors,
    ExpectedBenefitLevel,
)
from app.allocation.risk import (
    expected_unmet_demand,
    shortage_probability,
    marginal_benefit,
    classify_risk_level,
)
from app.allocation.optimizer import GreedyMarginalOptimizer


def validate_allocation(allocations: dict[str, int], budget: int = 60) -> None:
    """
    Strict validation of all hard competition constraints:
    1. Integer types
    2. Non-negative values
    3. Sum does not exceed budget
    """
    total = 0
    for d, x in allocations.items():
        if not isinstance(x, (int, np.integer)):
            raise ValueError(f"Constraint Violation: Allocation for {d} is non-integer: {x}")
        if x < 0:
            raise ValueError(f"Constraint Violation: Allocation for {d} is negative: {x}")
        total += int(x)

    if total > budget:
        raise ValueError(
            f"Constraint Violation: Total allocation {total} exceeds budget {budget}"
        )


def generate_explanation(
    district_id: str,
    allocated_reserve: int,
    forecast: float,
    capacity: int,
    sigma: float,
    surge_signal: float,
    policy: str,
) -> tuple[str, ExpectedBenefitLevel, AllocationFactors]:
    """
    Synthesizes genuine, calculated explanatory factors and reasons for an allocation.
    """
    prob = shortage_probability(forecast, capacity, 0.0, sigma)
    gap = max(0.0, forecast - capacity)
    u_base = expected_unmet_demand(forecast, capacity, 0.0, sigma)
    u_alloc = expected_unmet_demand(forecast, capacity, float(allocated_reserve), sigma)
    reduction = max(0.0, u_base - u_alloc)

    # Benefit level
    if reduction >= 6.0 or (prob >= 0.75 and allocated_reserve >= 5):
        benefit: ExpectedBenefitLevel = "High"
    elif reduction >= 1.5 or allocated_reserve >= 2:
        benefit = "Medium"
    else:
        benefit = "Low"

    # Normalized factors in [0, 1]
    norm_gap = float(np.clip(gap / 40.0, 0.0, 1.0))
    norm_prob = float(np.clip(prob, 0.0, 1.0))
    norm_surge = float(np.clip(surge_signal, 0.0, 1.0))
    fairness_urgency = float(np.clip(max(0.0, (forecast - capacity) / max(1.0, forecast)), 0.0, 1.0))

    factors = AllocationFactors(
        shortageRisk=round(norm_prob, 3),
        demandGap=round(norm_gap, 3),
        surgeSignal=round(norm_surge, 3),
        fairnessPriority=round(fairness_urgency, 3),
    )

    # Contextual reason
    if policy == "Equal Split":
        reason = "Equal baseline reserve distribution"
    elif norm_surge >= 0.5 and allocated_reserve > 0:
        reason = f"Online surge anomaly detected; proactive reserve boost (+{allocated_reserve} units)"
    elif norm_prob >= 0.8:
        reason = f"Critical shortage probability ({int(norm_prob * 100)}%); assigned {allocated_reserve} units to mitigate deficit"
    elif gap > 15:
        reason = f"High demand gap ({int(gap)} units); assigned {allocated_reserve} units"
    elif allocated_reserve > 0:
        reason = f"Protected district service ratio with {allocated_reserve} reserve units"
    else:
        reason = "Nominal capacity is sufficient; zero reserve required"

    return reason, benefit, factors


class ReserveAllocator:
    """
    Main Reserve Allocation System for HC-05.
    """

    def __init__(self, optimizer: GreedyMarginalOptimizer | None = None):
        self.optimizer = optimizer or GreedyMarginalOptimizer()

    def allocate(
        self,
        district_ids: Sequence[str],
        forecasts: dict[str, int | float],
        capacities: dict[str, int],
        sigmas: dict[str, float] | None = None,
        policy: AllocationPolicy = "Surge Adaptive",
        reserve_budget: int = 60,
        surge_signals: dict[str, float] | None = None,
        realized_demands: dict[str, int] | None = None,
    ) -> AllocationResult:
        """
        Execute reserve allocation for all districts under the specified policy.
        """
        sig_map = sigmas or {d: 8.0 for d in district_ids}
        s_signals = surge_signals or {d: 0.0 for d in district_ids}

        # Step 1: Compute Integer Allocations
        alloc_map = self.optimizer.allocate(
            district_ids=district_ids,
            forecasts=forecasts,
            capacities=capacities,
            sigmas=sig_map,
            reserve_budget=reserve_budget,
            surge_signals=s_signals,
            policy=policy,
        )

        # Step 2: Validate Hard Constraints
        validate_allocation(alloc_map, budget=reserve_budget)

        # Step 3: Compute District Allocations & Explanations
        district_allocations: list[DistrictAllocation] = []
        for d in district_ids:
            x_d = alloc_map[d]
            fc = float(forecasts[d])
            cap = capacities[d]
            sig = sig_map.get(d, 8.0)
            s_sig = s_signals.get(d, 0.0)

            reason, benefit, factors = generate_explanation(
                district_id=d,
                allocated_reserve=x_d,
                forecast=fc,
                capacity=cap,
                sigma=sig,
                surge_signal=s_sig,
                policy=policy,
            )

            district_allocations.append(
                DistrictAllocation(
                    districtId=d,
                    reserve=x_d,
                    reason=reason,
                    expectedBenefit=benefit,
                    factors=factors,
                )
            )

        # Step 4: Compute Resulting Outcomes
        # If realized demands are provided (post-revelation evaluation), use actuals.
        # Otherwise compute expected outcomes using predictive distributions.
        total_reserve = sum(alloc_map.values())
        reserve_utilization = float(total_reserve / max(1, reserve_budget))

        if realized_demands is not None:
            unmet_demands = {
                d: max(0, realized_demands[d] - capacities[d] - alloc_map[d])
                for d in district_ids
            }
            total_unmet = float(sum(unmet_demands.values()))
            total_demand = float(sum(realized_demands.values()))
            service_utility = max(0.0, 1.0 - (total_unmet / max(1.0, total_demand)))

            district_services = [
                max(0.0, 1.0 - (unmet_demands[d] / max(1.0, float(realized_demands[d]))))
                for d in district_ids
            ]
            worst_district_service = float(min(district_services)) if district_services else 1.0
        else:
            exp_unmets = {
                d: expected_unmet_demand(
                    float(forecasts[d]), capacities[d], float(alloc_map[d]), sig_map.get(d, 8.0)
                )
                for d in district_ids
            }
            total_unmet = float(sum(exp_unmets.values()))
            total_demand = float(sum(forecasts.values()))
            service_utility = max(0.0, 1.0 - (total_unmet / max(1.0, total_demand)))

            district_services = [
                max(0.0, 1.0 - (exp_unmets[d] / max(1.0, float(forecasts[d]))))
                for d in district_ids
            ]
            worst_district_service = float(min(district_services)) if district_services else 1.0

        return AllocationResult(
            policy=policy,
            totalReserve=total_reserve,
            allocations=district_allocations,
            totalUnmetDemand=round(total_unmet, 2),
            serviceUtility=round(service_utility, 4),
            worstDistrictService=round(worst_district_service, 4),
            reserveUtilization=round(reserve_utilization, 3),
        )
