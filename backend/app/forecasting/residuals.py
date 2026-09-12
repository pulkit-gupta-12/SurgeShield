"""
Residual Tracking and Diagnostics Subsystem.

Records realized errors (actual - forecast) chronologically per district,
calculates rolling bias and residual variance, and produces standardized Z-scores
to feed Phase 4 Online Surge Detection without contaminating the baseline forecast.
"""

from __future__ import annotations

import math
from typing import Sequence
import numpy as np
from pydantic import BaseModel, Field


class ResidualRecord(BaseModel):
    """Chronological record of a single forecasting event and realized error."""
    district_id: str
    month: int
    forecast: int
    actual: int
    residual: int          # actual - forecast
    absolute_error: int    # |actual - forecast|
    z_score: float = 0.0


class ResidualTracker:
    """
    In-memory stateful store for district-level forecasting residuals.
    """

    def __init__(self, default_sigma: float = 8.0):
        self.default_sigma = default_sigma
        # district_id -> list of ResidualRecord
        self.records_: dict[str, list[ResidualRecord]] = {}

    def record(
        self,
        district_id: str,
        month: int,
        forecast: int,
        actual: int,
    ) -> ResidualRecord:
        """
        Record an observed outcome, compute the residual and standardized Z-score.
        """
        residual = int(actual - forecast)
        abs_err = abs(residual)

        if district_id not in self.records_:
            self.records_[district_id] = []

        history = self.records_[district_id]
        
        # Calculate current variance before adding this point if history exists
        if len(history) >= 2:
            prev_resids = [r.residual for r in history]
            sigma = float(np.std(prev_resids, ddof=1))
            sigma = max(1.0, sigma)
        else:
            sigma = self.default_sigma

        z_score = float(residual / sigma)

        rec = ResidualRecord(
            district_id=district_id,
            month=month,
            forecast=int(forecast),
            actual=int(actual),
            residual=residual,
            absolute_error=abs_err,
            z_score=round(z_score, 4),
        )
        history.append(rec)
        return rec

    def get_records(self, district_id: str | None = None) -> list[ResidualRecord]:
        """Retrieve all records for a district or all districts."""
        if district_id is not None:
            return list(self.records_.get(district_id, []))
        all_recs = []
        for d_list in self.records_.values():
            all_recs.extend(d_list)
        return sorted(all_recs, key=lambda r: (r.month, r.district_id))

    def get_recent_mean(self, district_id: str, window: int = 3) -> float:
        """Rolling mean bias of the last `window` residuals for a district."""
        recs = self.records_.get(district_id, [])
        if not recs:
            return 0.0
        slice_recs = recs[-window:] if len(recs) >= window else recs
        return float(np.mean([r.residual for r in slice_recs]))

    def get_variance(self, district_id: str) -> float:
        """Empirical residual variance for a district."""
        recs = self.records_.get(district_id, [])
        if len(recs) < 2:
            return self.default_sigma ** 2
        return float(np.var([r.residual for r in recs], ddof=1))

    def get_std(self, district_id: str) -> float:
        """Empirical residual standard deviation for a district."""
        return math.sqrt(max(0.1, self.get_variance(district_id)))

    def get_latest_z_score(self, district_id: str) -> float:
        """Latest Z-score for district, or 0.0 if empty."""
        recs = self.records_.get(district_id, [])
        return recs[-1].z_score if recs else 0.0

    def is_anomaly(self, district_id: str, threshold: float = 2.0) -> bool:
        """Check whether the latest residual exceeds the anomaly Z-score threshold."""
        return self.get_latest_z_score(district_id) >= threshold

    def clear(self) -> None:
        """Reset all recorded residuals."""
        self.records_.clear()
