"""
Data Generator — HC-05 SurgeShield

Generates synthetic district health-demand data strictly conforming to the
HC-05 mathematical specification:
- 12 districts: D0–D11 (indices d = 0..11)
- 42 total months:
    - 36 historical months (t = 0..35)
    - 6 future / evaluation months (t = 36..41)
- District parameters:
    - b_d ~ Integer[60, 160] (sampled with rng.integers(60, 160, endpoint=True))
    - a_d ~ Uniform[10.0, 40.0]
    - g_d ~ Uniform[-0.5, 1.5]
- Demand equation for district d and month t:
    μ(d,t) = b_d + a_d * sin(2πt/12 + dπ/6) + g_d * t
    ε(d,t) ~ Normal(0, 8²)
    y(d,t) = max(0, round(μ(d,t) + ε(d,t)))
- Nominal district capacity:
    c_d = round(0.90 * b_d)
- Global monthly reserve:
    60 capacity units (unallocated by generator)
- Development-only surge:
    +35 demand units into D2 and D9 during t = 38, 39, 40
- Randomness:
    numpy.random.Generator(numpy.random.PCG64(seed))
    Default seed: 20260911

ONLINE EVALUATION ARCHITECTURAL PRINCIPLE:
------------------------------------------
The generator creates the full synthetic scenario (t=0..41) for benchmarking.
However, in sequential decision-making / online evaluation:
1. Forecasting and allocation modules must NEVER use future realized demand
   before the corresponding month is revealed (no data leakage).
2. The development surge (+35 to D2 and D9 at t=38..40) is for development,
   sanity checks, and baseline testing ONLY.
3. The final evaluation and allocation policies must NOT hard-code D2, D9, or
   months 38–40. Hidden test scenarios may inject surges into different
   districts at different months with different seeds.
"""

from __future__ import annotations

import math
from typing import Any, Sequence
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

# ── Specification Constants ───────────────────────────────────────────────────
DEFAULT_SEED: int = 20260911
DEFAULT_NUM_DISTRICTS: int = 12
DEFAULT_HISTORICAL_MONTHS: int = 36  # t = 0..35
DEFAULT_FUTURE_MONTHS: int = 6       # t = 36..41
DEFAULT_TOTAL_MONTHS: int = DEFAULT_HISTORICAL_MONTHS + DEFAULT_FUTURE_MONTHS  # 42
DEFAULT_RESERVE_CAPACITY: int = 60

# Development scenario surge parameters
DEFAULT_DEV_SURGE_DISTRICTS: tuple[str, str] = ("D2", "D9")
DEFAULT_DEV_SURGE_START: int = 38
DEFAULT_DEV_SURGE_DURATION: int = 3  # t = 38, 39, 40
DEFAULT_DEV_SURGE_AMOUNT: int = 35

# Parameter distributions
B_MIN: int = 60
B_MAX: int = 160  # inclusive
A_MIN: float = 10.0
A_MAX: float = 40.0
G_MIN: float = -0.5
G_MAX: float = 1.5
NOISE_STD: float = 8.0
CAPACITY_RATIO: float = 0.90


# ── Data Models ───────────────────────────────────────────────────────────────

class SurgeConfig(BaseModel):
    """
    Configuration for an additive demand surge.
    
    Attributes:
        districts: Target district IDs (e.g. ['D2', 'D9']).
        start_month: Starting month index (e.g. 38).
        duration: Number of consecutive months the surge lasts (e.g. 3 for t=38, 39, 40).
        amount: Additional demand units injected (e.g. 35).
    """
    districts: list[str] = Field(default_factory=lambda: list(DEFAULT_DEV_SURGE_DISTRICTS))
    start_month: int = DEFAULT_DEV_SURGE_START
    duration: int = DEFAULT_DEV_SURGE_DURATION
    amount: int = DEFAULT_DEV_SURGE_AMOUNT

    @classmethod
    def from_inputs(
        cls,
        districts: Sequence[int | str] | None = None,
        start_month: int = DEFAULT_DEV_SURGE_START,
        duration: int = DEFAULT_DEV_SURGE_DURATION,
        amount: int = DEFAULT_DEV_SURGE_AMOUNT,
    ) -> SurgeConfig:
        """Helper to create SurgeConfig supporting integer district indices or string IDs."""
        if districts is None:
            formatted_districts = list(DEFAULT_DEV_SURGE_DISTRICTS)
        else:
            formatted_districts = [
                f"D{d}" if isinstance(d, int) else str(d)
                for d in districts
            ]
        return cls(
            districts=formatted_districts,
            start_month=start_month,
            duration=duration,
            amount=amount,
        )


class DistrictParams(BaseModel):
    """
    HC-05 District Parameters.
    
    Attributes:
        district_id: Human-readable ID (e.g. 'D0', 'D1', ..., 'D11').
        district_index: Integer index d in [0..11].
        b_d: Baseline demand parameter ~ Integer[60, 160] (inclusive).
        a_d: Seasonality amplitude parameter ~ Uniform[10.0, 40.0].
        g_d: Demand growth/trend parameter ~ Uniform[-0.5, 1.5].
        nominal_capacity: District nominal capacity c_d = round(0.90 * b_d).
    """
    district_id: str
    district_index: int
    b_d: int
    a_d: float
    g_d: float
    nominal_capacity: int


class DistrictDemand(BaseModel):
    """
    Demand time series and components for a single district.
    
    Attributes:
        district_id: District identifier.
        district_index: District index d.
        params: District parameters and nominal capacity.
        base_demand: 42-month base demand before artificial surge.
        surge_demand: 42-month additive surge demand.
        total_demand: 42-month realized demand = base_demand + surge_demand.
        historical_demand: 36-month observed historical demand (t=0..35).
        future_demand: 6-month future demand (t=36..41).
        mean_demand: 42-month underlying mean demand μ(d,t).
        noise: 42-month Gaussian noise realizations ε(d,t).
    """
    district_id: str
    district_index: int
    params: DistrictParams
    base_demand: list[int]
    surge_demand: list[int]
    total_demand: list[int]
    historical_demand: list[int]
    future_demand: list[int]
    mean_demand: list[float]
    noise: list[float]


class GeneratedScenario(BaseModel):
    """
    Complete synthetic dataset and metadata generated for an HC-05 scenario.
    
    Holds strongly typed Python structures easily serializable to dict/JSON
    for FastAPI and downstream modules, while offering matrix and DataFrame
    accessors for vectorized computations.
    """
    seed: int
    num_districts: int = DEFAULT_NUM_DISTRICTS
    historical_months: int = DEFAULT_HISTORICAL_MONTHS
    future_months: int = DEFAULT_FUTURE_MONTHS
    total_months: int = DEFAULT_TOTAL_MONTHS
    reserve_capacity: int = DEFAULT_RESERVE_CAPACITY
    districts: list[str]
    district_indices: dict[str, int]
    params: dict[str, DistrictParams]
    capacities: dict[str, int]
    surge_config: SurgeConfig | None = None
    
    # Time series mappings (district_id -> list of values)
    historical_demand: dict[str, list[int]]
    future_demand: dict[str, list[int]]
    total_demand: dict[str, list[int]]
    base_demand: dict[str, list[int]]
    surge_demand: dict[str, list[int]]
    mean_demand: dict[str, list[float]]
    noise: dict[str, list[float]]
    
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ── Convenience Accessors ─────────────────────────────────────────────────

    def get_demand_matrix(self) -> np.ndarray:
        """Returns total/realized demand as a 2D NumPy array of shape (num_districts, total_months)."""
        return np.array([self.total_demand[d] for d in self.districts], dtype=int)

    def get_base_demand_matrix(self) -> np.ndarray:
        """Returns base demand (before surge) as a 2D NumPy array of shape (num_districts, total_months)."""
        return np.array([self.base_demand[d] for d in self.districts], dtype=int)

    def get_surge_matrix(self) -> np.ndarray:
        """Returns additive surge demand as a 2D NumPy array of shape (num_districts, total_months)."""
        return np.array([self.surge_demand[d] for d in self.districts], dtype=int)

    def get_historical_matrix(self) -> np.ndarray:
        """Returns observed historical demand as a 2D array of shape (num_districts, historical_months)."""
        return np.array([self.historical_demand[d] for d in self.districts], dtype=int)

    def get_future_matrix(self) -> np.ndarray:
        """Returns future demand as a 2D array of shape (num_districts, future_months)."""
        return np.array([self.future_demand[d] for d in self.districts], dtype=int)

    def get_mean_matrix(self) -> np.ndarray:
        """Returns underlying mean demand μ(d,t) as a 2D array of shape (num_districts, total_months)."""
        return np.array([self.mean_demand[d] for d in self.districts], dtype=float)

    def get_noise_matrix(self) -> np.ndarray:
        """Returns noise ε(d,t) as a 2D array of shape (num_districts, total_months)."""
        return np.array([self.noise[d] for d in self.districts], dtype=float)

    def get_district_demand(self, district_id_or_index: str | int) -> DistrictDemand:
        """Retrieve complete demand details for a specific district."""
        if isinstance(district_id_or_index, int):
            d_id = f"D{district_id_or_index}"
        else:
            d_id = str(district_id_or_index)
            
        if d_id not in self.params:
            raise KeyError(f"District {d_id} not found in scenario. Available: {self.districts}")
            
        return DistrictDemand(
            district_id=d_id,
            district_index=self.district_indices[d_id],
            params=self.params[d_id],
            base_demand=self.base_demand[d_id],
            surge_demand=self.surge_demand[d_id],
            total_demand=self.total_demand[d_id],
            historical_demand=self.historical_demand[d_id],
            future_demand=self.future_demand[d_id],
            mean_demand=self.mean_demand[d_id],
            noise=self.noise[d_id],
        )

    def to_dataframe(self) -> pd.DataFrame:
        """
        Flattens the scenario into a tidy pandas DataFrame with one row per (district, month).
        Ideal for analysis, visualization, and validation.
        """
        records = []
        for d in self.districts:
            params = self.params[d]
            for t in range(self.total_months):
                records.append({
                    "district_id": d,
                    "district_index": params.district_index,
                    "month": t,
                    "period": "historical" if t < self.historical_months else "future",
                    "base_demand": self.base_demand[d][t],
                    "surge_demand": self.surge_demand[d][t],
                    "total_demand": self.total_demand[d][t],
                    "mean_demand": self.mean_demand[d][t],
                    "noise": self.noise[d][t],
                    "nominal_capacity": params.nominal_capacity,
                    "b_d": params.b_d,
                    "a_d": params.a_d,
                    "g_d": params.g_d,
                })
        return pd.DataFrame.from_records(records)


# ── HC-05 Data Generator Implementation ───────────────────────────────────────

class HC05DataGenerator:
    """
    HC-05 Synthetic Health-Demand Data Generator.
    
    Guarantees:
    - Pure NumPy local RNG: numpy.random.Generator(numpy.random.PCG64(seed))
    - Zero global mutable state
    - Reproducible, deterministic scenario generation
    - Additive surge model: base demand and noise are strictly preserved,
      ensuring development_demand - base_demand == +35 only at the surge window.
    """

    def __init__(self, seed: int = DEFAULT_SEED):
        self.seed = seed
        self.rng = np.random.Generator(np.random.PCG64(seed))

    def generate(
        self,
        surge_config: SurgeConfig | None = None,
        num_districts: int = DEFAULT_NUM_DISTRICTS,
        historical_months: int = DEFAULT_HISTORICAL_MONTHS,
        future_months: int = DEFAULT_FUTURE_MONTHS,
        reserve_capacity: int = DEFAULT_RESERVE_CAPACITY,
    ) -> GeneratedScenario:
        """
        Generate a complete HC-05 synthetic scenario.
        
        Args:
            surge_config: Optional SurgeConfig. If None, base demand without surge is generated.
            num_districts: Number of districts (default 12: D0..D11).
            historical_months: Number of observed historical months (default 36: t=0..35).
            future_months: Number of future months in planning horizon (default 6: t=36..41).
            reserve_capacity: Global monthly reserve units (default 60).
            
        Returns:
            GeneratedScenario containing parameters, capacities, time series, and metadata.
        """
        total_months = historical_months + future_months
        district_ids = [f"D{d}" for d in range(num_districts)]
        district_indices = {f"D{d}": d for d in range(num_districts)}

        # ── 1. District Parameters ───────────────────────────────────────────
        # For each district independently:
        # b_d ~ Integer[60, 160] (endpoint=True ensures 160 is included)
        # a_d ~ Uniform[10.0, 40.0]
        # g_d ~ Uniform[-0.5, 1.5]
        # c_d = round(0.90 * b_d)
        params_dict: dict[str, DistrictParams] = {}
        capacities_dict: dict[str, int] = {}
        
        b_vec = np.zeros(num_districts, dtype=int)
        a_vec = np.zeros(num_districts, dtype=float)
        g_vec = np.zeros(num_districts, dtype=float)

        for d in range(num_districts):
            b_d = int(self.rng.integers(B_MIN, B_MAX, endpoint=True))
            a_d = float(self.rng.uniform(A_MIN, A_MAX))
            g_d = float(self.rng.uniform(G_MIN, G_MAX))
            c_d = int(round(CAPACITY_RATIO * b_d))
            
            b_vec[d] = b_d
            a_vec[d] = a_d
            g_vec[d] = g_d
            
            d_id = district_ids[d]
            dist_params = DistrictParams(
                district_id=d_id,
                district_index=d,
                b_d=b_d,
                a_d=a_d,
                g_d=g_d,
                nominal_capacity=c_d,
            )
            params_dict[d_id] = dist_params
            capacities_dict[d_id] = c_d

        # ── 2. Demand Mean Equation & Gaussian Noise ─────────────────────────
        # μ(d,t) = b_d + a_d * sin(2πt/12 + dπ/6) + g_d * t
        # ε(d,t) ~ Normal(0, 8²)
        # y_base(d,t) = max(0, round(μ(d,t) + ε(d,t)))
        mean_matrix = np.zeros((num_districts, total_months), dtype=float)
        noise_matrix = np.zeros((num_districts, total_months), dtype=float)
        base_demand_matrix = np.zeros((num_districts, total_months), dtype=int)

        # Generate noise matrix from local RNG instance (row-major order d=0..11, t=0..41)
        noise_matrix[:, :] = self.rng.normal(loc=0.0, scale=NOISE_STD, size=(num_districts, total_months))

        for d in range(num_districts):
            for t in range(total_months):
                seasonal_angle = (2.0 * math.pi * t / 12.0) + (d * math.pi / 6.0)
                mu_dt = b_vec[d] + a_vec[d] * math.sin(seasonal_angle) + g_vec[d] * t
                mean_matrix[d, t] = mu_dt
                
                # Realized base demand: max(0, round(μ + ε))
                val_with_noise = mu_dt + noise_matrix[d, t]
                base_demand_matrix[d, t] = max(0, int(round(val_with_noise)))

        # ── 3. Surge Injection (Additive Transformation) ───────────────────────
        # Conceptual pipeline:
        # seed -> parameters -> mean -> noise -> BASE demand -> copy -> optional surge -> TOTAL demand
        surge_matrix = np.zeros((num_districts, total_months), dtype=int)
        
        if surge_config is not None and surge_config.amount != 0 and surge_config.duration > 0:
            for d_str in surge_config.districts:
                if d_str in district_indices:
                    d_idx = district_indices[d_str]
                    t_start = max(0, surge_config.start_month)
                    t_end = min(total_months, surge_config.start_month + surge_config.duration)
                    for t in range(t_start, t_end):
                        surge_matrix[d_idx, t] += surge_config.amount

        total_demand_matrix = base_demand_matrix + surge_matrix

        # ── 4. Build Output Mappings ──────────────────────────────────────────
        historical_demand_dict: dict[str, list[int]] = {}
        future_demand_dict: dict[str, list[int]] = {}
        total_demand_dict: dict[str, list[int]] = {}
        base_demand_dict: dict[str, list[int]] = {}
        surge_demand_dict: dict[str, list[int]] = {}
        mean_demand_dict: dict[str, list[float]] = {}
        noise_dict: dict[str, list[float]] = {}

        for d in range(num_districts):
            d_id = district_ids[d]
            tot_list = [int(x) for x in total_demand_matrix[d, :]]
            base_list = [int(x) for x in base_demand_matrix[d, :]]
            surge_list = [int(x) for x in surge_matrix[d, :]]
            mean_list = [float(x) for x in mean_matrix[d, :]]
            noise_list = [float(x) for x in noise_matrix[d, :]]

            total_demand_dict[d_id] = tot_list
            base_demand_dict[d_id] = base_list
            surge_demand_dict[d_id] = surge_list
            historical_demand_dict[d_id] = tot_list[:historical_months]
            future_demand_dict[d_id] = tot_list[historical_months:]
            mean_demand_dict[d_id] = mean_list
            noise_dict[d_id] = noise_list

        metadata: dict[str, Any] = {
            "scenario_name": "HC-05 Health Demand Scenario",
            "generator": "HC05DataGenerator",
            "rng": "numpy.random.PCG64",
            "seed": self.seed,
            "has_surge": bool(surge_config is not None and surge_config.amount != 0),
            "surge_districts": surge_config.districts if surge_config else [],
            "surge_start": surge_config.start_month if surge_config else None,
            "surge_duration": surge_config.duration if surge_config else None,
            "surge_amount": surge_config.amount if surge_config else 0,
        }

        return GeneratedScenario(
            seed=self.seed,
            num_districts=num_districts,
            historical_months=historical_months,
            future_months=future_months,
            total_months=total_months,
            reserve_capacity=reserve_capacity,
            districts=district_ids,
            district_indices=district_indices,
            params=params_dict,
            capacities=capacities_dict,
            surge_config=surge_config,
            historical_demand=historical_demand_dict,
            future_demand=future_demand_dict,
            total_demand=total_demand_dict,
            base_demand=base_demand_dict,
            surge_demand=surge_demand_dict,
            mean_demand=mean_demand_dict,
            noise=noise_dict,
            metadata=metadata,
        )


# ── Functional Top-Level API ──────────────────────────────────────────────────

def generate_scenario(
    seed: int = DEFAULT_SEED,
    num_districts: int = DEFAULT_NUM_DISTRICTS,
    historical_months: int = DEFAULT_HISTORICAL_MONTHS,
    future_months: int = DEFAULT_FUTURE_MONTHS,
    reserve_capacity: int = DEFAULT_RESERVE_CAPACITY,
    surge_districts: Sequence[int | str] | None = None,
    surge_start: int = DEFAULT_DEV_SURGE_START,
    surge_duration: int = DEFAULT_DEV_SURGE_DURATION,
    surge_amount: int = DEFAULT_DEV_SURGE_AMOUNT,
    surge_config: SurgeConfig | None = None,
) -> GeneratedScenario:
    """
    Generate an HC-05 synthetic demand scenario with configurable surge.
    
    If neither surge_districts nor surge_config is supplied, a clean baseline
    scenario (no artificial surge) is returned.
    
    To inject a custom surge, provide surge_districts/start/duration/amount, or
    pass an explicit SurgeConfig instance.
    """
    if surge_config is None and surge_districts is not None:
        surge_config = SurgeConfig.from_inputs(
            districts=surge_districts,
            start_month=surge_start,
            duration=surge_duration,
            amount=surge_amount,
        )

    generator = HC05DataGenerator(seed=seed)
    return generator.generate(
        surge_config=surge_config,
        num_districts=num_districts,
        historical_months=historical_months,
        future_months=future_months,
        reserve_capacity=reserve_capacity,
    )


def generate_base_scenario(
    seed: int = DEFAULT_SEED,
    num_districts: int = DEFAULT_NUM_DISTRICTS,
    historical_months: int = DEFAULT_HISTORICAL_MONTHS,
    future_months: int = DEFAULT_FUTURE_MONTHS,
    reserve_capacity: int = DEFAULT_RESERVE_CAPACITY,
) -> GeneratedScenario:
    """
    Generate the unperturbed baseline HC-05 scenario (no artificial surge injected).
    """
    return generate_scenario(
        seed=seed,
        num_districts=num_districts,
        historical_months=historical_months,
        future_months=future_months,
        reserve_capacity=reserve_capacity,
        surge_districts=None,
        surge_config=None,
    )


def generate_development_scenario(
    seed: int = DEFAULT_SEED,
    num_districts: int = DEFAULT_NUM_DISTRICTS,
    historical_months: int = DEFAULT_HISTORICAL_MONTHS,
    future_months: int = DEFAULT_FUTURE_MONTHS,
    reserve_capacity: int = DEFAULT_RESERVE_CAPACITY,
) -> GeneratedScenario:
    """
    Generate the official HC-05 development scenario:
    Incorporate +35 units into D2 and D9 during months t = 38, 39, 40.
    
    Uses the exact same underlying randomness as generate_base_scenario(seed).
    """
    dev_surge = SurgeConfig(
        districts=list(DEFAULT_DEV_SURGE_DISTRICTS),
        start_month=DEFAULT_DEV_SURGE_START,
        duration=DEFAULT_DEV_SURGE_DURATION,
        amount=DEFAULT_DEV_SURGE_AMOUNT,
    )
    return generate_scenario(
        seed=seed,
        num_districts=num_districts,
        historical_months=historical_months,
        future_months=future_months,
        reserve_capacity=reserve_capacity,
        surge_config=dev_surge,
    )
