"""
Pydantic Schemas for Resource Allocation and Predictive Risk — HC-05 SurgeShield.
"""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

RiskLevel = Literal["Low", "Medium", "High", "Critical"]
AllocationPolicy = Literal[
    "Equal Split",
    "Forecast Only",
    "Risk Based",
    "Fairness Aware",
    "Surge Adaptive",
]
ExpectedBenefitLevel = Literal["Low", "Medium", "High"]


class AllocationFactors(BaseModel):
    """Normalized scoring factors explaining the allocation decision."""
    shortageRisk: float = Field(..., description="Estimated shortage probability in [0, 1]")
    demandGap: float = Field(..., description="Projected deficit over capacity normalized to [0, 1]")
    surgeSignal: float = Field(..., description="Online residual surge indicator in [0, 1]")
    fairnessPriority: float = Field(..., description="Fairness urgency score in [0, 1]")


class DistrictAllocation(BaseModel):
    """Allocation of emergency reserve units to a specific district."""
    districtId: str
    reserve: int = Field(..., ge=0, description="Allocated integer reserve units")
    reason: str
    expectedBenefit: ExpectedBenefitLevel
    factors: AllocationFactors


class DistrictRiskAssessment(BaseModel):
    """Detailed risk assessment for a district prior to or after allocation."""
    district_id: str
    forecast: int
    capacity: int
    uncertainty_sigma: float
    capacity_gap: int
    shortage_probability: float
    expected_unmet_baseline: float
    expected_unmet_allocated: float
    service_ratio_baseline: float
    service_ratio_allocated: float
    risk_level: RiskLevel


class AllocationResult(BaseModel):
    """Comprehensive result of an allocation cycle matching the frontend domain model."""
    policy: AllocationPolicy
    totalReserve: int = Field(..., description="Total reserve allocated (must be <= 60)")
    allocations: list[DistrictAllocation]
    totalUnmetDemand: float
    serviceUtility: float
    worstDistrictService: float
    reserveUtilization: float


class AllocationRequest(BaseModel):
    """Request payload for custom allocation execution."""
    forecasts: dict[str, int]
    capacities: dict[str, int]
    uncertainties: dict[str, float] | None = None
    policy: AllocationPolicy = "Surge Adaptive"
    reserve_budget: int = 60
    surge_signals: dict[str, float] | None = None
