"""
backend/routes/simulation.py — Project DRISHTI
==============================================
Simulation Endpoints:
Controls the real-time background transaction streamer for demonstration.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from backend.services.transaction_simulator import get_transaction_simulator

router = APIRouter(prefix="/api/simulation", tags=["Simulation"])


class StartSimRequest(BaseModel):
    interval_seconds: Optional[float] = Field(default=2.0, ge=0.5, le=30.0, description="Interval in seconds between simulated transactions")


@router.post("/start")
def start_simulation(req: StartSimRequest = StartSimRequest()):
    """
    Start the background synthetic transaction ingestion stream.
    Clearly marked as DEMO / SIMULATION MODE.
    """
    sim = get_transaction_simulator()
    return sim.start(interval_seconds=req.interval_seconds)


@router.post("/stop")
def stop_simulation():
    """
    Stop the background synthetic transaction ingestion stream.
    """
    sim = get_transaction_simulator()
    return sim.stop()


@router.get("/status")
def get_simulation_status():
    """
    Retrieve current status, rate, and recent simulated transactions.
    """
    sim = get_transaction_simulator()
    return sim.get_status()
