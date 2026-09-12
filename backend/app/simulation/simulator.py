"""
Simulation Engine — HC-05 SurgeShield.

Runs what-if simulation scenarios:
- Baseline
- Seasonal Peak (amplified seasonal wave)
- Demand Growth (accelerated upward trend)
- Sudden Surge (abrupt localized surge shocks)

Computes comparative outcomes across all allocation policies conforming to the frontend contract.
"""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel

from app.generator import (
    GeneratedScenario,
    generate_development_scenario,
    DEFAULT_SEED,
)
from app.allocation.schemas import AllocationPolicy
from app.allocation.allocator import ReserveAllocator
from app.forecasting import ForecastingEngine

SimulationScenario = Literal[
    "Baseline",
    "Seasonal Peak",
    "Demand Growth",
    "Sudden Surge",
]


class DistrictSimulationDetail(BaseModel):
    districtId: str
    allocation: int
    unmetDemand: int


class SimulationResult(BaseModel):
    policy: AllocationPolicy
    totalUnmetDemand: int
    serviceUtility: float
    worstDistrictService: float
    reserveUtilization: float
    districtAllocations: list[DistrictSimulationDetail]


class SimulationEngine:
    """
    Evaluates what-if capacity and policy stress tests.
    """

    def __init__(
        self,
        allocator: ReserveAllocator | None = None,
        forecaster: ForecastingEngine | None = None,
    ):
        self.allocator = allocator or ReserveAllocator()
        self.forecaster = forecaster or ForecastingEngine()

    def run_scenario(
        self,
        scenario_type: SimulationScenario = "Baseline",
        seed: int = DEFAULT_SEED,
        month: int = 36,
        reserve_budget: int = 60,
    ) -> list[SimulationResult]:
        """
        Executes all 5 policies against the selected simulation scenario at month t.
        """
        scenario = generate_development_scenario(seed=seed)
        districts = scenario.districts
        capacities = scenario.capacities

        # Determine scenario multipliers and surge injections
        multiplier = 1.0
        surge_boosts: dict[str, int] = {d: 0 for d in districts}

        if scenario_type == "Seasonal Peak":
            multiplier = 1.15
        elif scenario_type == "Demand Growth":
            multiplier = 1.25
        elif scenario_type == "Sudden Surge":
            # Add unexpected sudden shock to D2, D9 (+35)
            surge_boosts["D2"] = 35
            surge_boosts["D9"] = 35

        # Get forecasts using historical data up to month 35
        hist_matrix = scenario.get_historical_matrix()
        fc_res = self.forecaster.forecast_all_districts(
            historical_matrix=hist_matrix,
            capacities=capacities,
            district_ids=districts,
            horizon=1,
            start_month=month,
        )

        base_forecasts = {d: fc_res.districts[d].current_forecast for d in districts}
        sigmas = {d: fc_res.districts[d].uncertainty_std for d in districts}

        # Actual demands experienced under the scenario
        future_idx = max(0, min(month - 36, scenario.future_months - 1))
        actual_demands = {
            d: int(round(scenario.future_demand[d][future_idx] * multiplier + surge_boosts.get(d, 0)))
            for d in districts
        }

        # For policy allocation decisions:
        # Decisions only use legitimately observed past signals; zero clairvoyance
        surge_signals = {d: 0.0 for d in districts}

        policies: list[AllocationPolicy] = [
            "Equal Split",
            "Forecast Only",
            "Risk Based",
            "Fairness Aware",
            "Surge Adaptive",
        ]

        results: list[SimulationResult] = []

        for pol in policies:
            # Policy allocates based on forecast & signals
            alloc_res = self.allocator.allocate(
                district_ids=districts,
                forecasts=base_forecasts,
                capacities=capacities,
                sigmas=sigmas,
                policy=pol,
                reserve_budget=reserve_budget,
                surge_signals=surge_signals if pol == "Surge Adaptive" else None,
                realized_demands=actual_demands,
            )

            district_details = []
            for a in alloc_res.allocations:
                d = a.districtId
                eff_cap = capacities[d] + a.reserve
                unmet = max(0, actual_demands[d] - eff_cap)
                district_details.append(
                    DistrictSimulationDetail(
                        districtId=d,
                        allocation=a.reserve,
                        unmetDemand=unmet,
                    )
                )

            results.append(
                SimulationResult(
                    policy=pol,
                    totalUnmetDemand=int(alloc_res.totalUnmetDemand),
                    serviceUtility=alloc_res.serviceUtility,
                    worstDistrictService=alloc_res.worstDistrictService,
                    reserveUtilization=alloc_res.reserveUtilization,
                    districtAllocations=district_details,
                )
            )

        return results
