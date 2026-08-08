"""
event_recovery_routes.py
─────────────────────────
API Router exposing event ingestion simulation and timeline recovery endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from app.api.deps import get_current_user
from app.models.user import User
from app.services.event_recovery_simulator import EventRecoverySimulator

router = APIRouter()

@router.post("/simulate", status_code=status.HTTP_200_OK)
async def run_event_simulation(
    current_user: User = Depends(get_current_user),
):
    """Triggers adversarial streaming event recovery and verification checks."""
    sim = EventRecoverySimulator()
    stream = sim.generate_adversarial_stream()
    result = sim.process_with_recovery(stream)
    return result
