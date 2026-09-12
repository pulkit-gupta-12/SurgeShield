"""
Pydantic Schemas for Online Surge Detection — HC-05 SurgeShield.
"""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

from app.allocation.schemas import RiskLevel

SurgeStage = Literal[
    "Normal",
    "Elevated",
    "Anomaly",
    "Confirmed Surge",
    "Response",
]
ConfidenceLevel = Literal["Low", "Medium", "High"]


class SurgeAlert(BaseModel):
    """Surge alert event conforming to the frontend contract."""
    districtId: str
    stage: SurgeStage
    risk: RiskLevel
    expectedDemand: int
    observedDemand: int
    deviation: int
    confidence: ConfidenceLevel
    recommendedResponse: str
    timestamp: str


class DistrictSurgeStatus(BaseModel):
    """Diagnostic state for online surge tracking per district."""
    district_id: str
    stage: SurgeStage
    z_score: float
    rolling_bias: float
    consecutive_anomalies: int
    surge_signal_strength: float = Field(..., ge=0.0, le=1.0)
    estimated_surge_units: float
