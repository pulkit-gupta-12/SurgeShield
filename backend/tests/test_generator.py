"""
HC-05 SurgeShield — Comprehensive Test Suite for Phase 1 Data Generator

Verifies all HC-05 mathematical specifications, invariants, reproducibility,
and edge cases:
1. Exactly 12 districts generated.
2. District IDs are D0–D11.
3. Exactly 42 months generated.
4. Historical period is 0–35 (36 months).
5. Future period is 36–41 (6 months).
6. Demand values are non-negative integers.
7. b_d is within Integer[60, 160] (inclusive).
8. a_d is within Uniform[10, 40].
9. g_d is within Uniform[-0.5, 1.5].
10. Capacity follows round(0.90 * b_d).
11. Reserve is exactly 60.
12. Development surge adds exactly 35 to D2 and D9 at t=38,39,40.
13. No development surge is added outside those district/month combinations.
14. Deterministic generation: identical seed + config produces identical scenario.
15. Different seeds produce different generated scenarios.
16. Matrix dimensions (demand, historical, future, mean, noise).
17. Pydantic serialization / model dump.
18. Custom surge configuration.
19. DataFrame export structure and contents.
20. Underlying demand equation μ(d,t) and noise realization validation.
"""

import math
import numpy as np
import pytest

from app.generator import (
    DEFAULT_SEED,
    DEFAULT_NUM_DISTRICTS,
    DEFAULT_HISTORICAL_MONTHS,
    DEFAULT_FUTURE_MONTHS,
    DEFAULT_TOTAL_MONTHS,
    DEFAULT_RESERVE_CAPACITY,
    DEFAULT_DEV_SURGE_DISTRICTS,
    DEFAULT_DEV_SURGE_START,
    DEFAULT_DEV_SURGE_DURATION,
    DEFAULT_DEV_SURGE_AMOUNT,
    B_MIN,
    B_MAX,
    A_MIN,
    A_MAX,
    G_MIN,
    G_MAX,
    NOISE_STD,
    CAPACITY_RATIO,
    SurgeConfig,
    DistrictParams,
    DistrictDemand,
    GeneratedScenario,
    HC05DataGenerator,
    generate_scenario,
    generate_base_scenario,
    generate_development_scenario,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def base_scenario() -> GeneratedScenario:
    """Standard unperturbed scenario with default seed."""
    return generate_base_scenario(seed=DEFAULT_SEED)


@pytest.fixture
def dev_scenario() -> GeneratedScenario:
    """Official development scenario with default seed (+35 to D2, D9 at t=38..40)."""
    return generate_development_scenario(seed=DEFAULT_SEED)


# ── Test Cases ────────────────────────────────────────────────────────────────

def test_1_num_districts(base_scenario: GeneratedScenario):
    """1. Exactly 12 districts are generated."""
    assert len(base_scenario.districts) == 12
    assert len(base_scenario.params) == 12
    assert len(base_scenario.capacities) == 12
    assert len(base_scenario.total_demand) == 12


def test_2_district_ids(base_scenario: GeneratedScenario):
    """2. District IDs are D0–D11."""
    expected_ids = [f"D{d}" for d in range(12)]
    assert base_scenario.districts == expected_ids
    for d, d_id in enumerate(expected_ids):
        assert base_scenario.district_indices[d_id] == d
        assert base_scenario.params[d_id].district_id == d_id
        assert base_scenario.params[d_id].district_index == d


def test_3_total_months(base_scenario: GeneratedScenario):
    """3. Exactly 42 months are generated."""
    assert base_scenario.total_months == 42
    for d_id in base_scenario.districts:
        assert len(base_scenario.total_demand[d_id]) == 42
        assert len(base_scenario.base_demand[d_id]) == 42
        assert len(base_scenario.mean_demand[d_id]) == 42
        assert len(base_scenario.noise[d_id]) == 42


def test_4_historical_period(base_scenario: GeneratedScenario):
    """4. Historical period is 0–35 (36 months)."""
    assert base_scenario.historical_months == 36
    for d_id in base_scenario.districts:
        assert len(base_scenario.historical_demand[d_id]) == 36
        # Historical slice must match first 36 elements of total demand
        assert base_scenario.historical_demand[d_id] == base_scenario.total_demand[d_id][:36]


def test_5_future_period(base_scenario: GeneratedScenario):
    """5. Future period is 36–41 (6 months)."""
    assert base_scenario.future_months == 6
    for d_id in base_scenario.districts:
        assert len(base_scenario.future_demand[d_id]) == 6
        # Future slice must match elements 36..41 of total demand
        assert base_scenario.future_demand[d_id] == base_scenario.total_demand[d_id][36:]


def test_6_demand_values_non_negative_integers(base_scenario: GeneratedScenario, dev_scenario: GeneratedScenario):
    """6. Demand values are non-negative integers."""
    for scen in [base_scenario, dev_scenario]:
        for d_id in scen.districts:
            for t, val in enumerate(scen.total_demand[d_id]):
                assert isinstance(val, int), f"District {d_id}, month {t} is not an int: {type(val)}"
                assert val >= 0, f"District {d_id}, month {t} is negative: {val}"


def test_7_b_d_range(base_scenario: GeneratedScenario):
    """7. b_d is within the required range [60, 160]."""
    for d_id, param in base_scenario.params.items():
        assert isinstance(param.b_d, int)
        assert 60 <= param.b_d <= 160, f"{d_id}: b_d={param.b_d} outside [60, 160]"


def test_8_a_d_range(base_scenario: GeneratedScenario):
    """8. a_d is within [10.0, 40.0]."""
    for d_id, param in base_scenario.params.items():
        assert isinstance(param.a_d, float)
        assert 10.0 <= param.a_d <= 40.0, f"{d_id}: a_d={param.a_d} outside [10.0, 40.0]"


def test_9_g_d_range(base_scenario: GeneratedScenario):
    """9. g_d is within [-0.5, 1.5]."""
    for d_id, param in base_scenario.params.items():
        assert isinstance(param.g_d, float)
        assert -0.5 <= param.g_d <= 1.5, f"{d_id}: g_d={param.g_d} outside [-0.5, 1.5]"


def test_10_capacity_follows_formula(base_scenario: GeneratedScenario):
    """10. Capacity follows round(0.90 * b_d)."""
    for d_id, param in base_scenario.params.items():
        expected_capacity = int(round(0.90 * param.b_d))
        assert param.nominal_capacity == expected_capacity
        assert base_scenario.capacities[d_id] == expected_capacity


def test_11_reserve_is_exactly_60(base_scenario: GeneratedScenario):
    """11. Reserve is exactly 60."""
    assert base_scenario.reserve_capacity == 60


def test_12_and_13_development_surge_exact_and_isolated():
    """
    12. Development surge adds exactly 35 to D2 and D9 at t=38, 39, 40.
    13. No development surge is added outside those district/month combinations.
    
    Verifies that development scenario uses the EXACT same underlying randomness
    as base scenario: dev_demand - base_demand == +35 only at (D2, D9) and t in {38, 39, 40},
    and 0 everywhere else.
    """
    seed = DEFAULT_SEED
    base = generate_base_scenario(seed=seed)
    dev = generate_development_scenario(seed=seed)

    base_mat = base.get_demand_matrix()
    dev_mat = dev.get_demand_matrix()
    diff = dev_mat - base_mat

    # District indices for D2 (d=2) and D9 (d=9)
    surge_d_indices = {2, 9}
    surge_months = {38, 39, 40}

    for d in range(12):
        for t in range(42):
            if d in surge_d_indices and t in surge_months:
                assert diff[d, t] == 35, f"Expected +35 at d={d}, t={t}; got {diff[d, t]}"
            else:
                assert diff[d, t] == 0, f"Expected 0 diff at d={d}, t={t}; got {diff[d, t]}"

    # Also verify that base_demand stored in dev scenario matches base scenario total_demand exactly
    assert dev.get_base_demand_matrix().tolist() == base_mat.tolist()

    # And verify surge_matrix matches
    surge_mat = dev.get_surge_matrix()
    assert np.array_equal(surge_mat, diff)


def test_14_deterministic_same_seed():
    """14. Two generators using the same seed/configuration produce identical output."""
    scen1 = generate_development_scenario(seed=DEFAULT_SEED)
    scen2 = generate_development_scenario(seed=DEFAULT_SEED)

    # Test dictionaries and matrices equality
    assert scen1.get_demand_matrix().tolist() == scen2.get_demand_matrix().tolist()
    assert scen1.get_base_demand_matrix().tolist() == scen2.get_base_demand_matrix().tolist()
    assert scen1.get_mean_matrix().tolist() == scen2.get_mean_matrix().tolist()
    assert scen1.get_noise_matrix().tolist() == scen2.get_noise_matrix().tolist()

    for d_id in scen1.districts:
        p1 = scen1.params[d_id]
        p2 = scen2.params[d_id]
        assert p1.b_d == p2.b_d
        assert p1.a_d == p2.a_d
        assert p1.g_d == p2.g_d
        assert p1.nominal_capacity == p2.nominal_capacity


def test_15_different_seeds_produce_different_scenarios():
    """15. Different seeds produce different generated scenarios."""
    scen1 = generate_scenario(seed=20260911)
    scen2 = generate_scenario(seed=12345678)

    # District parameters and demand must differ
    mat1 = scen1.get_demand_matrix()
    mat2 = scen2.get_demand_matrix()
    assert not np.array_equal(mat1, mat2)

    b1 = [p.b_d for p in scen1.params.values()]
    b2 = [p.b_d for p in scen2.params.values()]
    assert b1 != b2


def test_16_matrix_dimensions(base_scenario: GeneratedScenario):
    """16. Matrix accessors have expected shapes and types."""
    assert base_scenario.get_demand_matrix().shape == (12, 42)
    assert base_scenario.get_base_demand_matrix().shape == (12, 42)
    assert base_scenario.get_surge_matrix().shape == (12, 42)
    assert base_scenario.get_historical_matrix().shape == (12, 36)
    assert base_scenario.get_future_matrix().shape == (12, 6)
    assert base_scenario.get_mean_matrix().shape == (12, 42)
    assert base_scenario.get_noise_matrix().shape == (12, 42)


def test_17_serialization(dev_scenario: GeneratedScenario):
    """17. GeneratedScenario and models serialize cleanly to Python dict."""
    dumped = dev_scenario.model_dump()
    assert isinstance(dumped, dict)
    assert dumped["seed"] == DEFAULT_SEED
    assert len(dumped["districts"]) == 12
    assert "D0" in dumped["params"]
    assert "D2" in dumped["total_demand"]
    assert dumped["reserve_capacity"] == 60


def test_18_custom_surge_configuration():
    """18. Custom surge configuration works generically for arbitrary districts and months."""
    custom_surge = SurgeConfig(
        districts=["D5", "D10"],
        start_month=37,
        duration=2,  # t=37, 38
        amount=25,
    )
    base = generate_base_scenario(seed=999)
    custom = generate_scenario(seed=999, surge_config=custom_surge)

    diff = custom.get_demand_matrix() - base.get_demand_matrix()
    surge_d_indices = {5, 10}
    surge_months = {37, 38}

    for d in range(12):
        for t in range(42):
            if d in surge_d_indices and t in surge_months:
                assert diff[d, t] == 25
            else:
                assert diff[d, t] == 0


def test_19_dataframe_export(dev_scenario: GeneratedScenario):
    """19. to_dataframe() returns valid DataFrame with 504 rows (12 districts * 42 months)."""
    df = dev_scenario.to_dataframe()
    assert len(df) == 12 * 42  # 504 rows
    expected_cols = {
        "district_id", "district_index", "month", "period",
        "base_demand", "surge_demand", "total_demand",
        "mean_demand", "noise", "nominal_capacity",
        "b_d", "a_d", "g_d",
    }
    assert expected_cols.issubset(set(df.columns))

    # Verify period labels
    assert (df[df["month"] < 36]["period"] == "historical").all()
    assert (df[df["month"] >= 36]["period"] == "future").all()


def test_20_demand_equation_and_noise_exactness(base_scenario: GeneratedScenario):
    """
    20. Verify mathematical demand equation:
    μ(d,t) = b_d + a_d * sin(2πt/12 + dπ/6) + g_d * t
    y(d,t) = max(0, round(μ + ε))
    """
    for d, d_id in enumerate(base_scenario.districts):
        p = base_scenario.params[d_id]
        for t in range(42):
            expected_mu = p.b_d + p.a_d * math.sin(2.0 * math.pi * t / 12.0 + d * math.pi / 6.0) + p.g_d * t
            actual_mu = base_scenario.mean_demand[d_id][t]
            assert pytest.approx(actual_mu, rel=1e-10) == expected_mu

            noise = base_scenario.noise[d_id][t]
            expected_y = max(0, int(round(expected_mu + noise)))
            actual_y = base_scenario.total_demand[d_id][t]
            assert actual_y == expected_y
