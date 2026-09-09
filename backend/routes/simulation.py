"""
backend/routes/simulation.py — Project DRISHTI
==============================================
Simulation Endpoints:
Controls the real-time background transaction streamer for demonstration.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
from backend.services.transaction_simulator import get_transaction_simulator
from backend.auth.security import get_current_user

router = APIRouter(prefix="/api/simulation", tags=["Simulation"])


class StartSimRequest(BaseModel):
    interval_seconds: Optional[float] = Field(default=2.0, ge=0.5, le=30.0, description="Interval in seconds between simulated transactions")


@router.post("/start")
def start_simulation(req: StartSimRequest = StartSimRequest(), current_user: dict = Depends(get_current_user)):
    """
    Start the background synthetic transaction ingestion stream.
    Clearly marked as DEMO / SIMULATION MODE.
    """
    sim = get_transaction_simulator()
    return sim.start(interval_seconds=req.interval_seconds)


@router.post("/stop")
def stop_simulation(current_user: dict = Depends(get_current_user)):
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
