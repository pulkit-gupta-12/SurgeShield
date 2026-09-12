"""
Sequential Online Evaluation Engine — HC-05 SurgeShield.

Simulates months 36 -> 41 with strict sequential information revelation:
1. Forecast month t using history strictly up to t-1
2. Assess risk and retrieve any surge signals detected from past residuals
3. Optimize 60 emergency reserve units for month t
4. Enforce hard constraints
5. REVEAL actual demand at month t
6. Compute unmet demand and residual
7. Update residual tracker and online surge detector
8. Repeat for next month
"""

from __future__ import annotations

import time
from typing import Sequence
import numpy as np
from pydantic import BaseModel

from app.generator import GeneratedScenario
from app.forecasting import ForecastingEngine
from app.allocation import ReserveAllocator, AllocationResult, AllocationPolicy
from app.surge import OnlineSurgeDetector, SurgeAlert
from app.evaluation.metrics import (
    compute_competition_scorecard,
    CompetitionScorecard,
    ComplianceStatus,
)


class MonthlyCycleLog(BaseModel):
    month: int
    forecasts: dict[str, int]
    allocations: dict[str, int]
    actuals: dict[str, int]
    residuals: dict[str, int]
    unmets: dict[str, int]
    active_surge_signals: dict[str, float]
    alerts_generated: list[SurgeAlert]


class SequentialEvaluationResult(BaseModel):
    policy: AllocationPolicy
    scorecard: CompetitionScorecard
    cycle_logs: list[MonthlyCycleLog]
    runtime_seconds: float


class SequentialEvaluator:
    """
    Online Sequential Evaluator guaranteeing zero data leakage.
    """

    def __init__(
        self,
        forecasting_engine: ForecastingEngine | None = None,
        allocator: ReserveAllocator | None = None,
        surge_detector: OnlineSurgeDetector | None = None,
    ):
        self.engine = forecasting_engine or ForecastingEngine()
        self.allocator = allocator or ReserveAllocator()
        self.detector = surge_detector or OnlineSurgeDetector()

    def evaluate_scenario(
        self,
        scenario: GeneratedScenario,
        policy: AllocationPolicy = "Surge Adaptive",
        forecasting_model: str = "harmonic_regression",
        reserve_budget: int = 60,
    ) -> SequentialEvaluationResult:
        """
        Executes the 6-month online sequential evaluation (months 36..41).
        """
        start_time = time.perf_counter()
        self.detector.reset()

        districts = scenario.districts
        capacities = scenario.capacities
        horizon = scenario.future_months  # 6 months: t = 36..41
        start_month = scenario.historical_months  # 36

        # Historical series (initially t = 0..35)
        # We copy this so we can expand history strictly month-by-month as actuals are revealed
        dynamic_history: dict[str, list[int]] = {
            d: list(scenario.historical_demand[d]) for d in districts
        }

        # matrices to record for official competition scoring
        recorded_forecasts: dict[str, list[int]] = {d: [] for d in districts}
        recorded_actuals: dict[str, list[int]] = {d: [] for d in districts}
        recorded_allocations: dict[str, list[int]] = {d: [] for d in districts}

        cycle_logs: list[MonthlyCycleLog] = []
        compliance = ComplianceStatus(
            reserveConstraint=True,
            integerAllocations=True,
            noFutureLeakage=True,
            reproducibleConfig=True,
        )

        for step in range(horizon):
            current_month = start_month + step

            # Step 1: Forecast next month t using history strictly up to t-1
            # Note: zero future information is passed to forecaster
            fc_dict: dict[str, int] = {}
            sigma_dict: dict[str, float] = {}

            for d in districts:
                history_so_far = dynamic_history[d]
                # Guarantee history length equals current_month
                if len(history_so_far) != current_month:
                    compliance.noFutureLeakage = False

                fc_res = self.engine.forecast_district(
                    district_id=d,
                    history=history_so_far,
                    horizon=1,
                    capacity=capacities[d],
                    model_type=forecasting_model,
                    start_month=current_month,
                )
                fc_val = fc_res.future[0].forecast
                fc_dict[d] = fc_val
                sigma_dict[d] = fc_res.uncertainty_std

            # Step 2: Retrieve surge signals legitimately detected from past observations
            surge_signals = self.detector.get_surge_signals(districts)

            # Step 3: Optimize reserve allocation for month t
            alloc_res: AllocationResult = self.allocator.allocate(
                district_ids=districts,
                forecasts=fc_dict,
                capacities=capacities,
                sigmas=sigma_dict,
                policy=policy,
                reserve_budget=reserve_budget,
                surge_signals=surge_signals,
            )

            # Step 4: Verify hard constraints
            alloc_dict = {a.districtId: a.reserve for a in alloc_res.allocations}
            total_allocated = sum(alloc_dict.values())

            if total_allocated > reserve_budget:
                compliance.reserveConstraint = False
            for val in alloc_dict.values():
                if not isinstance(val, int) or val < 0:
                    compliance.integerAllocations = False

            # Step 5: REVEAL actual realized demand for month t (unveiled only after allocation!)
            actual_dict: dict[str, int] = {
                d: scenario.future_demand[d][step] for d in districts
            }

            # Step 6: Compute realized unmet demand and residuals
            unmet_dict: dict[str, int] = {}
            residual_dict: dict[str, int] = {}
            step_alerts: list[SurgeAlert] = []

            for d in districts:
                act = actual_dict[d]
                fc = fc_dict[d]
                cap = capacities[d]
                res = alloc_dict[d]

                eff_cap = cap + res
                unmet = max(0, act - eff_cap)
                unmet_dict[d] = unmet
                residual = act - fc
                residual_dict[d] = residual

                # Step 7: Update online surge detector with realized residual
                alert = self.detector.observe(
                    district_id=d,
                    month=current_month,
                    forecast=fc,
                    actual=act,
                    capacity=cap,
                )
                step_alerts.append(alert)

                # Step 8: Update dynamic history for the next cycle
                dynamic_history[d].append(act)

                # Store into full matrices
                recorded_forecasts[d].append(fc)
                recorded_actuals[d].append(act)
                recorded_allocations[d].append(res)

            cycle_logs.append(
                MonthlyCycleLog(
                    month=current_month,
                    forecasts=fc_dict,
                    allocations=alloc_dict,
                    actuals=actual_dict,
                    residuals=residual_dict,
                    unmets=unmet_dict,
                    active_surge_signals=surge_signals,
                    alerts_generated=step_alerts,
                )
            )

        elapsed = time.perf_counter() - start_time

        # Step 9: Compute final competition scorecard
        scorecard = compute_competition_scorecard(
            actuals_matrix=recorded_actuals,
            forecasts_matrix=recorded_forecasts,
            allocations_matrix=recorded_allocations,
            capacities=capacities,
            compliance=compliance,
            runtime_seconds=elapsed,
            start_month=start_month,
        )

        return SequentialEvaluationResult(
            policy=policy,
            scorecard=scorecard,
            cycle_logs=cycle_logs,
            runtime_seconds=round(elapsed, 4),
        )
