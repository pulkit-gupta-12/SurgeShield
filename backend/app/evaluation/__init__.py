"""
Evaluation Package — HC-05 SurgeShield.
"""

from app.evaluation.metrics import (
    ComplianceStatus,
    DistrictServiceRecord,
    TimelinePoint,
    CompetitionScorecard,
    compute_forecast_utility,
    compute_unmet_demand,
    compute_service_utility,
    compute_district_service_ratios,
    compute_worst_district_utility,
    compute_competition_scorecard,
)
from app.evaluation.sequential import (
    MonthlyCycleLog,
    SequentialEvaluationResult,
    SequentialEvaluator,
)
from app.evaluation.baselines import (
    POLICIES,
    PolicyBenchmarkComparison,
    MultiSeedSummary,
    benchmark_all_policies,
    summarize_benchmarks,
    run_multi_seed_stress_test,
)

__all__ = [
    "ComplianceStatus",
    "DistrictServiceRecord",
    "TimelinePoint",
    "CompetitionScorecard",
    "compute_forecast_utility",
    "compute_unmet_demand",
    "compute_service_utility",
    "compute_district_service_ratios",
    "compute_worst_district_utility",
    "compute_competition_scorecard",
    "MonthlyCycleLog",
    "SequentialEvaluationResult",
    "SequentialEvaluator",
    "POLICIES",
    "PolicyBenchmarkComparison",
    "MultiSeedSummary",
    "benchmark_all_policies",
    "summarize_benchmarks",
    "run_multi_seed_stress_test",
]
