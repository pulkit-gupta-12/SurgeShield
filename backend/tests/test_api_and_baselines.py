"""
Unit Tests for Phase 6 FastAPI Endpoints, What-If Simulation, and Multi-Seed Benchmarks.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.generator import DEFAULT_SEED
from app.evaluation import run_multi_seed_stress_test

client = TestClient(app)


def test_1_api_health():
    """Verify health endpoint."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "harmonic_regression" in data["models_available"]


def test_2_api_districts():
    """Verify districts listing and single district endpoint."""
    res = client.get("/api/districts")
    assert res.status_code == 200
    districts = res.json()
    assert len(districts) == 12
    assert districts[0]["id"] == "D0"

    res_single = client.get("/api/districts/D0")
    assert res_single.status_code == 200
    assert res_single.json()["id"] == "D0"

    res_detail = client.get("/api/districts/D0/detail")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert "effectiveCapacity" in detail
    assert "serviceLevel" in detail


def test_3_api_allocations():
    """Verify allocation endpoint enforces budget and integers."""
    res = client.get("/api/allocations?policy=Surge%20Adaptive")
    assert res.status_code == 200
    data = res.json()
    assert data["policy"] == "Surge Adaptive"
    assert data["totalReserve"] <= 60
    assert len(data["allocations"]) == 12

    total = sum(a["reserve"] for a in data["allocations"])
    assert total <= 60
    for a in data["allocations"]:
        assert isinstance(a["reserve"], int)
        assert a["reserve"] >= 0
        assert "shortageRisk" in a["factors"]


def test_4_api_surge_alerts_and_history():
    """Verify surge detection alerts and district residual history."""
    res_alerts = client.get("/api/surge-alerts")
    assert res_alerts.status_code == 200
    alerts = res_alerts.json()
    assert len(alerts) >= 12

    res_hist = client.get("/api/surge-alerts/D0/history")
    assert res_hist.status_code == 200
    hist = res_hist.json()
    assert len(hist) <= 12


def test_5_api_performance_and_baselines():
    """Verify official competition scorecard and baseline benchmarks."""
    res_perf = client.get("/api/performance")
    assert res_perf.status_code == 200
    perf = res_perf.json()
    assert "forecastUtility" in perf
    assert "demandServiceUtility" in perf
    assert "worstDistrictService" in perf
    assert perf["compliance"]["reserveConstraint"] is True

    res_base = client.get("/api/performance/baselines")
    assert res_base.status_code == 200
    baselines = res_base.json()
    assert len(baselines) == 5


def test_6_api_simulation_and_sequential():
    """Verify what-if simulation and sequential runs."""
    res_sim = client.post("/api/simulation", json={"scenario": "Sudden Surge"})
    assert res_sim.status_code == 200
    sim_results = res_sim.json()
    assert len(sim_results) == 5

    res_seq = client.post("/api/simulation/sequential?policy=Surge%20Adaptive")
    assert res_seq.status_code == 200
    seq_data = res_seq.json()
    assert "scorecard" in seq_data
    assert len(seq_data["cycle_logs"]) == 6


def test_7_multi_seed_stress_testing():
    """Multi-seed stress test across multiple seeds to ensure robustness."""
    test_seeds = [20260911, 20260912, 20260913]
    summaries = run_multi_seed_stress_test(seeds=test_seeds, policies=["Surge Adaptive", "Equal Split"])

    for pol in ("Surge Adaptive", "Equal Split"):
        s = summaries[pol]
        assert s.u_forecast_mean >= 0.90
        assert s.u_service_mean >= 0.70
        assert s.u_worst_mean >= 0.50
        assert s.runtime_mean < 2.0
