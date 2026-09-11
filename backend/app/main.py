"""
HC-05 SurgeShield — FastAPI Backend (Placeholder)

This is a placeholder FastAPI application. The actual forecasting,
allocation, surge detection, simulation and evaluation logic will be
implemented here and connected to the frontend service layer.

Run: uvicorn app.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SurgeShield API",
    description="HC-05 District Health Surge Forecast & Allocation",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "SurgeShield API", "version": "0.1.0"}


# TODO: Implement the following endpoints
# GET  /api/districts
# GET  /api/districts/{district_id}
# GET  /api/forecasts
# GET  /api/forecasts/{district_id}
# GET  /api/allocations?policy={policy}
# GET  /api/surge-alerts
# GET  /api/surge-alerts/{district_id}/history
# GET  /api/surge-residuals/{district_id}
# GET  /api/performance
# POST /api/simulation
