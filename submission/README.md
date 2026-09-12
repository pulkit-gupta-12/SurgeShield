# SurgeShield — Submission README

## Problem Statement
**HC-05: District Health Surge Forecast and Allocation**

SurgeShield is an automated predictive-optimization platform designed for health emergency management. It coordinates health resource allocation across 12 interdependent geographic districts over a 6-month sequential horizon ($t=36 \dots 41$) subject to a strict aggregate resource constraint of 60 units/month, operational capacity limits, and stochastic disease surge outbreaks.

---

## Submission Artifacts

The `submission/` directory contains exactly four official deliverables:

1. **`month_by_month_results.csv`**:
   - Sequential, step-by-step decision audit across all 12 districts for months $t=36, 37, 38, 39, 40, 41$ (72 district-month rows + header).
   - Generated strictly under the online protocol: **Forecast $\to$ Allocate $\to$ Observe $\to$ Detect $\to$ Adapt**.
   - Contains: `month`, `district`, `forecast`, `capacity`, `allocation`, `actual_demand`, `unmet_demand`, `risk`, `policy`.
   - **Zero future-demand leakage**: All allocation decisions are made prior to revealing actual monthly demand. Every monthly allocation strictly sums to $\le 60$ integer units.

2. **`district_results.csv`**:
   - Comprehensive district-level performance summary for all 12 districts (12 rows + header).
   - Computed directly from the official evaluation pipeline on the development benchmark scenario (`seed=20260911`).
   - Contains: `district`, `total_forecast`, `total_actual`, `total_allocation`, `total_unmet`, `service_utility`, `forecast_error`, `risk_status`.

3. **`approach.pdf`**:
   - Comprehensive technical submission document covering:
     1. Problem Statement & Operational Constraints
     2. Synthetic Health Demand Generator & Epidemiology
     3. Forecasting Subsystem (Triple Ensemble: Ridge + RF + GBR)
     4. Uncertainty & Risk Estimation
     5. Two-Tier Reserve Allocation Strategy
     6. Fairness-Aware Allocation (Minimax Shortfall Optimization)
     7. Online Surge Detection (CUSUM & Z-score)
     8. Sequential Decision Process (Zero Leakage)
     9. Competition Evaluation Metric (100-pt Scorecard)
     10. Baseline Policy Comparison & 20-Seed Robustness
     11. Reproducibility & Seed Protocol
     12. Real-World Limitations & Deployment Roadmap

4. **`README.md`**:
   - This submission guide and execution manual.

5. **`notebooks/`**:
   - `01_data_generation.ipynb`: Data generator, district parameters, capacity deficits, and surge injection.
   - `02_forecasting.ipynb`: Harmonic regression, rolling-origin cross-validation, and 90% uncertainty intervals.
   - `03_allocation.ipynb`: Constrained resource allocation, marginal benefits, and minimax fairness optimization.
   - `04_evaluation.ipynb`: Sequential evaluation simulation, official 100-pt scorecard, and 20-seed robustness.

---

## Verified Evaluation & Robustness Benchmarks

- **Selected Production Policy**: `Fairness Aware` (Tiered Reserve + Minimax Shortfall Optimization)
- **Official Score Formula**:
  $$\text{Score} = 30 \times U_{\text{forecast}} + 40 \times U_{\text{service}} + 30 \times U_{\text{worst}} \in [0, 100]$$
- **Development Seed (`20260911`) Score**: **81.75 / 100**
  - Forecast Utility: $0.9282$
  - Aggregate Service Utility: $0.7566$
  - Worst-District Utility: $0.6573$ ($D_9$)
  - Total Unmet Demand: 2,457 (out of 10,093 demand across 6 months)
- **20-Seed Robustness Evaluation (`seed=20260911` to `20260930`)**:
  - `Fairness Aware`: **84.02 ± 1.96** (Worst-District: $0.6904 \pm 0.0347$)
  - `Proportional to Forecast`: **81.56 ± 1.83** (Worst-District: $0.6272 \pm 0.0390$)
  - `Priority Heuristic`: **80.32 ± 1.79** (Worst-District: $0.6120 \pm 0.0410$)
  - `Equal Split`: **75.40 ± 1.84** (Worst-District: $0.5765 \pm 0.0425$)
- **Automated Verification**: **85 passing unit & integration tests** in `backend/tests/`.

---

## Important Source Code Paths

- **Synthetic Generator**:
  [`backend/app/generator/generator.py`](file:///backend/app/generator/generator.py) — 12-district spatio-temporal stochastic generator with seasonal epidemics, gravity mobility, and unannounced surge triggers.
- **Forecasting Subsystem**:
  [`backend/app/forecasting/`](file:///backend/app/forecasting/) — Feature engineering, Triple-model ensemble (Ridge, Random Forest, Gradient Boosting), conformal prediction intervals, and multi-step recursive forecaster.
- **Allocation Subsystem**:
  [`backend/app/allocation/`](file:///backend/app/allocation/) — Dynamic safety reserve, LP/MILP minimax shortfall optimization, integer rounded allocation with exact budget enforcement ($\sum a_i \le 60$).
- **Surge Detection Subsystem**:
  [`backend/app/simulation/surge.py`](file:///backend/app/simulation/surge.py) — Online dual-mode detection (Z-score + CUSUM cumulative sum tracking).
- **Sequential Evaluation Pipeline**:
  [`backend/app/evaluation/`](file:///backend/app/evaluation/) — Official 100-point scoring engine, multi-policy benchmark suite, and leakage-free sequential rolling simulation runner.
- **Simulation Runner**:
  [`backend/app/simulation/`](file:///backend/app/simulation/) — Turn-by-turn simulation harness coordinating forecast, allocation, revelation, and feedback.
- **Backend Test Suite**:
  [`backend/tests/`](file:///backend/tests/) — 85 unit, integration, mathematical invariant, and zero-leakage test cases.

---

## Dependencies

### Backend (Python 3.10+)
- `fastapi` & `uvicorn` — REST API service
- `numpy` & `pandas` — Numerical data processing
- `scipy` — Statistical distributions and optimization
- `scikit-learn` — Ridge regression, Random Forest, Gradient Boosting
- `pydantic` — Strict request/response schemas
- `pytest` — Automated testing suite
- `reportlab` — PDF compilation

To install all backend dependencies:
```bash
cd backend
pip install -r requirements.txt
pip install reportlab  # if not already installed
```

### Frontend (Node.js 18+)
- `react` 19, `vite`, `lucide-react`, `recharts`
```bash
cd frontend
npm install
```

---

## How to Run the Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## How to Run the Frontend Dashboard

```bash
cd frontend
npm run dev
```
- Local Dashboard: [http://localhost:5173](http://localhost:5173)

---

## How to Run the Automated Tests

Run the complete test suite from the `backend/` directory:
```bash
cd backend
pytest -v
```
All 85 tests verify:
- Non-negative, integer allocations with total $\le 60$
- Zero future-leakage (allocations cannot access unrevealed ground truth)
- Mathematical monotonicity and minimax optimality
- Reproducibility across seeds

---

## Reproducibility Instructions

To reproduce the submission CSV files and evaluation scores directly via Python:

```bash
cd backend
python -c "
from app.evaluation.evaluator import Evaluator
from app.simulation.runner import SimulationRunner

evaluator = Evaluator()
runner = SimulationRunner()
results = runner.run_evaluation(policy='fairness_aware', seed=20260911)
metrics = evaluator.evaluate(results['history'])
print('Score:', metrics['total_score'])
print('Worst Utility:', metrics['worst_district_utility'])
"
```
Output:
```text
Score: 81.75
Worst Utility: 0.6573
```
