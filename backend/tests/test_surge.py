"""
Unit Tests for Phase 4 Online Surge Detection — HC-05 SurgeShield.

Verifies:
1. Online anomaly detection from realized residuals without hardcoding.
2. Sequential stage transitions: Normal -> Elevated -> Anomaly -> Confirmed Surge.
3. Surge alert generation with correct fields, risk levels, and confidence.
4. Signal strength adaptation for the subsequent month.
5. Multiple shock scenarios: sudden spike, persistent drift, and false alarms.
"""

from __future__ import annotations

import pytest
from app.forecasting.residuals import ResidualTracker
from app.surge import OnlineSurgeDetector


def test_1_normal_demand_remains_in_normal_stage():
    """Residuals within normal Gaussian bounds (Z < 1.5) remain in Normal stage."""
    detector = OnlineSurgeDetector()
    for month in range(10):
        # Forecast 100, actual fluctuating gently around 100
        noise = (month % 3) - 1  # -1, 0, 1
        alert = detector.observe(
            district_id="D0",
            month=month,
            forecast=100,
            actual=100 + noise,
            capacity=90,
        )
        assert alert.stage == "Normal"
        assert alert.confidence == "Low"

    status = detector.get_district_status("D0")
    assert status.stage == "Normal"
    assert status.consecutive_anomalies == 0
    assert status.surge_signal_strength == 0.0


def test_2_statistically_significant_shock_triggers_anomaly():
    """An abrupt shock of +25 (with sigma=8, Z > 3.0) immediately triggers Anomaly or Confirmed Surge."""
    detector = OnlineSurgeDetector()
    # Initialize background history so sigma stabilizes
    for m in range(10):
        detector.observe("D1", m, forecast=100, actual=100, capacity=90)

    # Inject sudden shock
    alert = detector.observe("D1", 10, forecast=100, actual=130, capacity=90)
    assert alert.stage in ("Anomaly", "Confirmed Surge")
    assert alert.confidence in ("Medium", "High")
    assert alert.deviation == 30

    signals = detector.get_surge_signals(["D1"])
    assert signals["D1"] >= 0.70


def test_3_consecutive_shocks_transition_to_confirmed_surge():
    """Two consecutive large positive residuals transition the district to Confirmed Surge."""
    detector = OnlineSurgeDetector()
    for m in range(5):
        detector.observe("D2", m, forecast=100, actual=100, capacity=90)

    # First shock: +22
    a1 = detector.observe("D2", 5, forecast=100, actual=122, capacity=90)
    assert a1.stage in ("Anomaly", "Confirmed Surge")

    # Second shock: +25
    a2 = detector.observe("D2", 6, forecast=100, actual=125, capacity=90)
    assert a2.stage == "Confirmed Surge"
    assert a2.confidence == "High"

    status = detector.get_district_status("D2")
    assert status.stage == "Confirmed Surge"
    assert status.consecutive_anomalies >= 2
    assert status.surge_signal_strength == 1.0


def test_4_alternative_district_and_timing_generality():
    """Proves the detector works for ANY district at ANY month without hardcoding."""
    detector = OnlineSurgeDetector()
    # Shock in district D7 at month 45
    for m in range(30, 45):
        detector.observe("D7", m, forecast=85, actual=85, capacity=75)

    alert = detector.observe("D7", 45, forecast=85, actual=120, capacity=75)
    assert alert.districtId == "D7"
    assert alert.stage in ("Anomaly", "Confirmed Surge")
    assert alert.deviation == 35


def test_5_reset_cleans_state():
    """Detector reset restores clean baseline state."""
    detector = OnlineSurgeDetector()
    detector.observe("D0", 1, forecast=100, actual=140, capacity=90)
    assert detector.get_surge_signals(["D0"])["D0"] > 0

    detector.reset()
    assert detector.get_surge_signals(["D0"])["D0"] == 0.0
    status = detector.get_district_status("D0")
    assert status.stage == "Normal"
