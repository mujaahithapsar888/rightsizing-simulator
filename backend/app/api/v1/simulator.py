"""
simulator.py — Simulation API Router
──────────────────────────────────────
POST  /run              Run a rightsizing simulation (ML-powered)
GET   /runs             List all simulation runs
GET   /runs/{id}        Get single run
GET   /runs/{id}/timeseries  Get CPU/Memory time-series for charts
DELETE /runs/{id}       Delete a run
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import get_current_user
from app.core.database import AsyncSession, get_db
from app.models.metric import MetricDataset, MetricRecord
from app.models.simulation import SimulationRun
from app.models.user import User
from app.schemas.simulator import SimulationConfig, SimulationResultOut, SimulationRunList
from app.services.rightsizing_engine import run_rightsizing_analysis

router = APIRouter()


async def _load_dataset_series(
    dataset_id: uuid.UUID,
    db: AsyncSession,
    time_window_hours: int,
) -> Dict[str, List]:
    """Load CPU, memory, latency and timestamps from a MetricDataset."""
    # Pull up to time_window_hours worth of records ordered by timestamp
    result = await db.execute(
        select(
            MetricRecord.timestamp,
            MetricRecord.cpu_utilization,
            MetricRecord.memory_utilization,
            MetricRecord.latency_ms,
            MetricRecord.request_volume,
        )
        .where(MetricRecord.dataset_id == dataset_id)
        .order_by(MetricRecord.timestamp.asc())
        .limit(time_window_hours * 10)  # up to 10 records per hour
    )
    rows = result.all()

    if not rows:
        return {"cpu": [], "memory": [], "latency": [], "request_volume": [], "timestamps": []}

    return {
        "cpu":            [r.cpu_utilization for r in rows if r.cpu_utilization is not None],
        "memory":         [r.memory_utilization for r in rows if r.memory_utilization is not None],
        "latency":        [r.latency_ms for r in rows if r.latency_ms is not None],
        "request_volume": [r.request_volume for r in rows if r.request_volume is not None],
        "timestamps":     [r.timestamp.isoformat() for r in rows],
    }


# ─── POST /run ────────────────────────────────────────────────────────────────

@router.post("/run", response_model=SimulationResultOut, status_code=status.HTTP_201_CREATED)
async def run_simulation(
    config: SimulationConfig,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Run a rightsizing simulation.

    If a dataset_id is supplied and the dataset is ready, the analysis
    is driven by actual CPU/Memory telemetry. Otherwise a conservative
    synthetic distribution is used.
    """
    cpu_series: Optional[List[float]] = None
    memory_series: Optional[List[float]] = None
    timestamps: Optional[List[str]] = None
    data_driven = False

    if config.dataset_id:
        ds_result = await db.execute(
            select(MetricDataset).where(MetricDataset.id == config.dataset_id)
        )
        dataset = ds_result.scalar_one_or_none()

        if dataset and dataset.status == "ready":
            series = await _load_dataset_series(config.dataset_id, db, config.time_window_hours)
            if series["cpu"]:
                cpu_series = series["cpu"]
                memory_series = series["memory"]
                timestamps = series["timestamps"]
                data_driven = True

    # Run the Baseline engine (optionally ML-driven)
    from app.services.baseline_engine import run_baseline_analysis
    results = run_baseline_analysis(
        config=config,
        cpu_series=cpu_series,
        memory_series=memory_series,
        latency_series=series.get("latency") if config.dataset_id and dataset and dataset.status == "ready" else None,
        availability_series=None,
        timestamps=timestamps
    )

    # Persist the run
    run = SimulationRun(
        name=config.name,
        description=config.description,
        dataset_id=config.dataset_id,
        config=config.model_dump(mode="json"),
        results=results,
        status="completed",
        created_by=current_user.id,
        completed_at=datetime.now(timezone.utc),
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


# ─── GET /runs ────────────────────────────────────────────────────────────────

@router.get("/runs", response_model=SimulationRunList)
async def list_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_result = await db.execute(select(func.count()).select_from(SimulationRun))
    total = total_result.scalar_one()

    result = await db.execute(
        select(SimulationRun)
        .order_by(SimulationRun.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    items = result.scalars().all()
    return SimulationRunList(total=total, items=list(items))


# ─── GET /runs/{id} ───────────────────────────────────────────────────────────

@router.get("/runs/{run_id}", response_model=SimulationResultOut)
async def get_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(SimulationRun).where(SimulationRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    return run


# ─── GET /runs/{id}/timeseries ────────────────────────────────────────────────

@router.get("/runs/{run_id}/timeseries")
async def get_run_timeseries(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Return the raw CPU/Memory time-series used for a simulation run.
    Used by the frontend charts.
    """
    result = await db.execute(select(SimulationRun).where(SimulationRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")

    if not run.dataset_id:
        return {"timestamps": [], "cpu": [], "memory": [], "latency": [], "request_volume": [], "data_driven": False}

    cfg = run.config
    time_window = cfg.get("time_window_hours", 168)
    series = await _load_dataset_series(run.dataset_id, db, time_window)
    return {**series, "data_driven": len(series["cpu"]) > 0}


# ─── DELETE /runs/{id} ───────────────────────────────────────────────────────

@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(SimulationRun).where(SimulationRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    await db.delete(run)
    await db.commit()
