"""
Predictive Risk Estimation Engine — HC-05 SurgeShield.

Computes exact expected unmet demand, shortage probabilities, and discrete marginal benefits
using calibrated predictive uncertainty distributions.
"""

from __future__ import annotations

import math
import numpy as np
from scipy.stats import norm

from app.allocation.schemas import DistrictRiskAssessment, RiskLevel


SQRT_2 = math.sqrt(2.0)
INV_SQRT_2PI = 1.0 / math.sqrt(2.0 * math.pi)


def standard_normal_pdf(z: float) -> float:
    """Standard normal probability density function: phi(z)."""
    return INV_SQRT_2PI * math.exp(-0.5 * z * z)


def standard_normal_cdf(z: float) -> float:
    """Standard normal cumulative distribution function: Phi(z)."""
    return 0.5 * (1.0 + math.erf(z / SQRT_2))


def standard_normal_loss(z: float) -> float:
    """
    Standard normal loss function L(z) = phi(z) - z * (1 - Phi(z)).
    Represents E[max(0, Z - z)] where Z ~ Normal(0, 1).
    Numerically stable for extreme values of z.
    """
    if z < -7.0:
        return -z
    if z > 7.0:
        return 0.0
    phi = standard_normal_pdf(z)
    cdf = standard_normal_cdf(z)
    return phi - z * (1.0 - cdf)


def expected_unmet_demand(
    forecast: float,
    capacity: float,
    reserve: float = 0.0,
    sigma: float = 8.0,
) -> float:
    """
    Calculates exact expected unmet demand E[max(0, Y - (capacity + reserve))]
    assuming Y ~ Normal(forecast, sigma^2).
    """
    eff_cap = capacity + reserve
    sig = max(0.1, float(sigma))
    z = (eff_cap - forecast) / sig
    unmet = sig * standard_normal_loss(z)
    return max(0.0, float(unmet))


def shortage_probability(
    forecast: float,
    capacity: float,
    reserve: float = 0.0,
    sigma: float = 8.0,
) -> float:
    """
    Calculates probability that demand exceeds available capacity: P(Y > capacity + reserve).
    """
    eff_cap = capacity + reserve
    sig = max(0.1, float(sigma))
    z = (eff_cap - forecast) / sig
    prob = 1.0 - standard_normal_cdf(z)
    return float(np.clip(prob, 0.0, 1.0))


def marginal_benefit(
    forecast: float,
    capacity: float,
    current_reserve: int,
    sigma: float = 8.0,
) -> float:
    """
    Marginal reduction in expected unmet demand achieved by adding one more reserve unit:
    MB(x) = E[u(x)] - E[u(x + 1)].
    """
    u_curr = expected_unmet_demand(forecast, capacity, float(current_reserve), sigma)
    u_next = expected_unmet_demand(forecast, capacity, float(current_reserve + 1), sigma)
    return max(0.0, float(u_curr - u_next))


def classify_risk_level(
    forecast: float,
    capacity: float,
    shortage_prob: float,
    expected_unmet: float,
) -> RiskLevel:
    """
    Hierarchical risk classification into Low, Medium, High, or Critical.
    Considers capacity gap, shortage probability, and expected unmet demand.
    """
    gap = forecast - capacity
    if gap >= 25 or shortage_prob >= 0.85 or expected_unmet >= 20:
        return "Critical"
    if gap >= 12 or shortage_prob >= 0.60 or expected_unmet >= 10:
        return "High"
    if gap >= 0 or shortage_prob >= 0.35 or expected_unmet >= 3:
        return "Medium"
    return "Low"


def assess_district_risk(
    district_id: str,
    forecast: int,
    capacity: int,
    sigma: float = 8.0,
    allocated_reserve: int = 0,
) -> DistrictRiskAssessment:
    """
    Generates a full risk diagnostic profile for a district before and after reserve allocation.
    """
    gap = forecast - capacity
    prob = shortage_probability(forecast, capacity, 0.0, sigma)
    unmet_base = expected_unmet_demand(forecast, capacity, 0.0, sigma)
    unmet_alloc = expected_unmet_demand(forecast, capacity, float(allocated_reserve), sigma)

    safe_forecast = max(1.0, float(forecast))
    ratio_base = max(0.0, 1.0 - (unmet_base / safe_forecast))
    ratio_alloc = max(0.0, 1.0 - (unmet_alloc / safe_forecast))
    risk_level = classify_risk_level(forecast, capacity, prob, unmet_base)

    return DistrictRiskAssessment(
        district_id=district_id,
        forecast=int(forecast),
        capacity=int(capacity),
        uncertainty_sigma=round(float(sigma), 3),
        capacity_gap=int(gap),
        shortage_probability=round(float(prob), 4),
        expected_unmet_baseline=round(float(unmet_base), 3),
        expected_unmet_allocated=round(float(unmet_alloc), 3),
        service_ratio_baseline=round(float(ratio_base), 4),
        service_ratio_allocated=round(float(ratio_alloc), 4),
        risk_level=risk_level,
    )
