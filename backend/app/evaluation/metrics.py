"""
Evaluation Metrics — HC-05 SurgeShield.

Implements exact competition evaluation metrics:
- Forecast Utility (U_forecast): 30 points
- Demand-Service Utility (U_service): 45 points
- Worst-District Service (U_worst): 15 points
- Compliance Checks: 5 points
- Runtime & Reproducibility: 5 points
"""

from __future__ import annotations

from typing import Sequence, Any
import numpy as np
from pydantic import BaseModel, Field


class ComplianceStatus(BaseModel):
    reserveConstraint: bool = True
    integerAllocations: bool = True
    noFutureLeakage: bool = True
    reproducibleConfig: bool = True

    @property
    def all_passed(self) -> bool:
        return (
            self.reserveConstraint
            and self.integerAllocations
            and self.noFutureLeakage
            and self.reproducibleConfig
        )


class DistrictServiceRecord(BaseModel):
    districtId: str
    service: float


class TimelinePoint(BaseModel):
    month: int
    demand: int
    capacity: int
    reserve: int
    unmet: int


class CompetitionScorecard(BaseModel):
    forecastUtility: float = Field(..., ge=0.0, le=1.0)
    demandServiceUtility: float = Field(..., ge=0.0, le=1.0)
    worstDistrictService: float = Field(..., ge=0.0, le=1.0)
    compliance: ComplianceStatus
    totalUnmetDemand: int
    totalDemand: int
    totalScore: float = Field(..., ge=0.0, le=100.0)
    districtService: list[DistrictServiceRecord]
    unmetDemandTimeline: list[TimelinePoint]
    runtimeSeconds: float = 0.0


def compute_forecast_utility(
    actuals: Sequence[int | float] | np.ndarray,
    forecasts: Sequence[int | float] | np.ndarray,
) -> float:
    """
    Computes exact competition Forecast Utility:
    U_forecast = 1 - sum(|y - y_hat|) / sum(max(y, 1)), clipped to [0, 1].
    """
    y = np.asarray(actuals, dtype=float)
    y_hat = np.asarray(forecasts, dtype=float)

    if len(y) == 0:
        return 1.0

    abs_errors = np.abs(y - y_hat)
    denominators = np.maximum(y, 1.0)

    sum_abs_err = float(np.sum(abs_errors))
    sum_denom = float(np.sum(denominators))

    if sum_denom <= 0:
        return 1.0

    raw_utility = 1.0 - (sum_abs_err / sum_denom)
    return float(np.clip(raw_utility, 0.0, 1.0))


def compute_unmet_demand(
    actual: int | float,
    capacity: int,
    allocation: int,
) -> int:
    """
    Realized unmet demand for a district at a given month:
    u = max(0, actual - (capacity + allocation)).
    """
    effective_capacity = capacity + allocation
    return max(0, int(round(actual - effective_capacity)))


def compute_service_utility(
    actuals: Sequence[int | float] | np.ndarray,
    unmets: Sequence[int | float] | np.ndarray,
) -> float:
    """
    Computes exact competition Service Utility:
    U_service = 1 - sum(unmet) / sum(max(actual, 1)), clipped to [0, 1].
    """
    y = np.asarray(actuals, dtype=float)
    u = np.asarray(unmets, dtype=float)

    if len(y) == 0:
        return 1.0

    denominators = np.maximum(y, 1.0)
    sum_unmet = float(np.sum(u))
    sum_denom = float(np.sum(denominators))

    if sum_denom <= 0:
        return 1.0

    raw_utility = 1.0 - (sum_unmet / sum_denom)
    return float(np.clip(raw_utility, 0.0, 1.0))


def compute_district_service_ratios(
    district_actuals: dict[str, list[int]],
    district_unmets: dict[str, list[int]],
) -> dict[str, float]:
    """
    Computes service ratio r_d for each district over the evaluation horizon:
    r_d = 1 - sum_t(unmet_d,t) / sum_t(max(actual_d,t, 1)).
    """
    ratios: dict[str, float] = {}
    for d, act_list in district_actuals.items():
        unmet_list = district_unmets.get(d, [0] * len(act_list))
        y = np.asarray(act_list, dtype=float)
        u = np.asarray(unmet_list, dtype=float)

        sum_denom = float(np.sum(np.maximum(y, 1.0)))
        sum_u = float(np.sum(u))

        if sum_denom <= 0:
            ratios[d] = 1.0
        else:
            ratios[d] = float(np.clip(1.0 - (sum_u / sum_denom), 0.0, 1.0))
    return ratios


def compute_worst_district_utility(district_ratios: dict[str, float]) -> float:
    """
    Computes U_worst = min_d (r_d).
    """
    if not district_ratios:
        return 1.0
    return float(min(district_ratios.values()))


def compute_competition_scorecard(
    actuals_matrix: dict[str, list[int]],
    forecasts_matrix: dict[str, list[int]],
    allocations_matrix: dict[str, list[int]],
    capacities: dict[str, int],
    compliance: ComplianceStatus | None = None,
    runtime_seconds: float = 0.0,
    start_month: int = 36,
) -> CompetitionScorecard:
    """
    Computes the complete, official 100-point competition scorecard.
    """
    districts = sorted(actuals_matrix.keys())
    horizon = len(next(iter(actuals_matrix.values())))

    all_actuals = []
    all_forecasts = []
    all_unmets = []
    district_unmets: dict[str, list[int]] = {d: [] for d in districts}

    monthly_timelines: list[TimelinePoint] = []

    for t_idx in range(horizon):
        month = start_month + t_idx
        m_demand = 0
        m_cap = 0
        m_res = 0
        m_unmet = 0

        for d in districts:
            act = actuals_matrix[d][t_idx]
            fc = forecasts_matrix[d][t_idx]
            res = allocations_matrix[d][t_idx]
            cap = capacities[d]
            unmet = compute_unmet_demand(act, cap, res)

            all_actuals.append(act)
            all_forecasts.append(fc)
            all_unmets.append(unmet)
            district_unmets[d].append(unmet)

            m_demand += act
            m_cap += cap
            m_res += res
            m_unmet += unmet

        monthly_timelines.append(
            TimelinePoint(
                month=month,
                demand=m_demand,
                capacity=m_cap,
                reserve=m_res,
                unmet=m_unmet,
            )
        )

    u_fc = compute_forecast_utility(all_actuals, all_forecasts)
    u_srv = compute_service_utility(all_actuals, all_unmets)
    d_ratios = compute_district_service_ratios(actuals_matrix, district_unmets)
    u_worst = compute_worst_district_utility(d_ratios)

    comp = compliance or ComplianceStatus()
    comp_points = 5.0 if comp.all_passed else 0.0
    runtime_points = 5.0 if runtime_seconds <= 5.0 else max(1.0, 5.0 - runtime_seconds)

    # Official scoring: 30 * U_fc + 45 * U_srv + 15 * U_worst + 5 * comp + 5 * runtime
    raw_total = (
        30.0 * u_fc
        + 45.0 * u_srv
        + 15.0 * u_worst
        + comp_points
        + runtime_points
    )
    total_score = float(np.clip(raw_total, 0.0, 100.0))

    district_records = [
        DistrictServiceRecord(districtId=d, service=round(d_ratios[d], 4))
        for d in districts
    ]

    return CompetitionScorecard(
        forecastUtility=round(u_fc, 4),
        demandServiceUtility=round(u_srv, 4),
        worstDistrictService=round(u_worst, 4),
        compliance=comp,
        totalUnmetDemand=int(sum(all_unmets)),
        totalDemand=int(sum(all_actuals)),
        totalScore=round(total_score, 2),
        districtService=district_records,
        unmetDemandTimeline=monthly_timelines,
        runtimeSeconds=round(runtime_seconds, 4),
    )
