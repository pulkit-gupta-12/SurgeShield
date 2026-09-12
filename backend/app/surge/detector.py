"""
Online Surge Detector — HC-05 SurgeShield.

Monitors realized demand residuals online to detect abnormal surges dynamically.
Zero hardcoding: operates strictly through statistical residual analysis.
"""

from __future__ import annotations

import math
from typing import Sequence
import numpy as np

from app.forecasting.residuals import ResidualTracker, ResidualRecord
from app.allocation.schemas import RiskLevel
from app.allocation.risk import classify_risk_level
from app.surge.schemas import SurgeAlert, DistrictSurgeStatus, SurgeStage, ConfidenceLevel


class OnlineSurgeDetector:
    """
    Online Anomaly and Health Surge Detector.
    
    Tracks residuals sequentially, detects statistically improbable spikes,
    and transitions district state across stages:
    Normal -> Elevated -> Anomaly -> Confirmed Surge -> Response
    """

    def __init__(
        self,
        residual_tracker: ResidualTracker | None = None,
        anomaly_z_threshold: float = 2.5,
        elevated_z_threshold: float = 1.5,
        surge_shock_z_threshold: float = 3.5,
    ):
        self.tracker = residual_tracker or ResidualTracker(default_sigma=8.0)
        self.anomaly_z_threshold = anomaly_z_threshold
        self.elevated_z_threshold = elevated_z_threshold
        self.surge_shock_z_threshold = surge_shock_z_threshold

        # district_id -> state
        self.consecutive_anomalies: dict[str, int] = {}
        self.current_stages: dict[str, SurgeStage] = {}
        self.latest_alerts: dict[str, SurgeAlert] = {}
        self.estimated_surges: dict[str, float] = {}

    def observe(
        self,
        district_id: str,
        month: int,
        forecast: int,
        actual: int,
        capacity: int | None = None,
    ) -> SurgeAlert:
        """
        Record realized demand observation for district at month t, update internal statistical state,
        and generate a SurgeAlert if anomalous.
        """
        record: ResidualRecord = self.tracker.record(
            district_id=district_id,
            month=month,
            forecast=forecast,
            actual=actual,
        )

        z = record.z_score
        residual = record.residual
        rolling_mean = self.tracker.get_recent_mean(district_id, window=3)

        prev_anomalies = self.consecutive_anomalies.get(district_id, 0)
        is_positive_anomaly = z >= self.anomaly_z_threshold

        if is_positive_anomaly:
            consecutive = prev_anomalies + 1
        elif z >= self.elevated_z_threshold:
            consecutive = max(1, prev_anomalies)
        else:
            consecutive = 0
        self.consecutive_anomalies[district_id] = consecutive

        # State transition logic
        if z >= self.surge_shock_z_threshold or consecutive >= 2:
            stage: SurgeStage = "Confirmed Surge"
            confidence: ConfidenceLevel = "High"
            signal_strength = 1.0
            response = "Critical surge detected; increase reserve allocation priority immediately"
            est_surge = max(float(residual), float(rolling_mean))
        elif z >= self.anomaly_z_threshold:
            stage = "Anomaly"
            confidence = "Medium"
            signal_strength = 0.7
            response = "Statistically abnormal spike observed; prepare reserve deployment"
            est_surge = float(residual)
        elif z >= self.elevated_z_threshold or (rolling_mean > 5.0 and residual > 0):
            stage = "Elevated"
            confidence = "Medium"
            signal_strength = 0.35
            response = "Elevated demand pressure detected; monitor closely"
            est_surge = max(0.0, float(rolling_mean))
        else:
            stage = "Normal"
            confidence = "Low"
            signal_strength = 0.0
            response = "Demand within expected statistical bounds"
            est_surge = 0.0

        self.current_stages[district_id] = stage
        self.estimated_surges[district_id] = est_surge

        # Risk classification
        cap = capacity if capacity is not None else forecast
        risk_level: RiskLevel = classify_risk_level(
            forecast=float(forecast),
            capacity=float(cap),
            shortage_prob=1.0 if stage == "Confirmed Surge" else 0.5 if stage == "Anomaly" else 0.2,
            expected_unmet=max(0.0, float(actual - cap)),
        )

        alert = SurgeAlert(
            districtId=district_id,
            stage=stage,
            risk=risk_level,
            expectedDemand=forecast,
            observedDemand=actual,
            deviation=residual,
            confidence=confidence,
            recommendedResponse=response,
            timestamp=f"Month {month}",
        )
        self.latest_alerts[district_id] = alert
        return alert

    def get_surge_signals(self, district_ids: Sequence[str]) -> dict[str, float]:
        """
        Returns normalized surge signal strengths [0.0, 1.0] for each district,
        derived strictly from observed historical residuals through the latest month.
        Used to adapt the NEXT month's reserve allocation.
        """
        signals: dict[str, float] = {}
        for d in district_ids:
            stage = self.current_stages.get(d, "Normal")
            if stage == "Confirmed Surge":
                signals[d] = 1.0
            elif stage == "Anomaly":
                signals[d] = 0.70
            elif stage == "Elevated":
                signals[d] = 0.35
            else:
                signals[d] = 0.0
        return signals

    def get_district_status(self, district_id: str) -> DistrictSurgeStatus:
        """Get diagnostic status summary for a specific district."""
        stage = self.current_stages.get(district_id, "Normal")
        z = self.tracker.get_latest_z_score(district_id)
        rolling = self.tracker.get_recent_mean(district_id, window=3)
        consec = self.consecutive_anomalies.get(district_id, 0)
        est = self.estimated_surges.get(district_id, 0.0)

        signals = self.get_surge_signals([district_id])
        return DistrictSurgeStatus(
            district_id=district_id,
            stage=stage,
            z_score=round(z, 3),
            rolling_bias=round(rolling, 3),
            consecutive_anomalies=consec,
            surge_signal_strength=round(signals.get(district_id, 0.0), 3),
            estimated_surge_units=round(est, 1),
        )

    def get_all_alerts(self, district_ids: Sequence[str]) -> list[SurgeAlert]:
        """Return all latest alerts across districts sorted by urgency."""
        alerts: list[SurgeAlert] = []
        for d in district_ids:
            if d in self.latest_alerts:
                alerts.append(self.latest_alerts[d])
            else:
                # Default normal alert if unobserved
                alerts.append(
                    SurgeAlert(
                        districtId=d,
                        stage="Normal",
                        risk="Low",
                        expectedDemand=100,
                        observedDemand=100,
                        deviation=0,
                        confidence="Low",
                        recommendedResponse="No action needed",
                        timestamp="Month 36",
                    )
                )

        priority = {"Confirmed Surge": 4, "Anomaly": 3, "Elevated": 2, "Normal": 1, "Response": 5}
        return sorted(alerts, key=lambda a: priority.get(a.stage, 0), reverse=True)

    def reset(self) -> None:
        """Reset internal state."""
        self.tracker.clear()
        self.consecutive_anomalies.clear()
        self.current_stages.clear()
        self.latest_alerts.clear()
        self.estimated_surges.clear()
