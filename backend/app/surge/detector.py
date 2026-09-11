"""
Surge Detector — HC-05

Online anomaly detection from observed demand residuals:
- Residual = Actual − Forecast
- Detects unusual positive deviations
- Stages: Normal → Elevated → Anomaly → Confirmed Surge → Response

Important: surge location/timing is hidden during evaluation.
Detection must rely on residuals, not prior knowledge.
"""
