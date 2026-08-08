"""
experiments.py — Updated Experiments API Router
─────────────────────────────────────────────────
Integrates with the scenario_simulator engine. Exposes endpoints to evaluate
scenarios (Normal Weekday, Live Sports, Viral Video) with traffic growth,
SLA thresholds, custom instance pricing parameters, and sensitivity analyses.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from app.api.deps import get_current_user
from app.core.database import AsyncSession, get_db
from app.models.experiment import Experiment
from app.models.metric import MetricDataset, MetricRecord
from app.models.user import User
from app.schemas.experiment import ExperimentList, ExperimentOut
from app.services.scenario_simulator import simulate_scenario

router = APIRouter()

class PricingOverride(BaseModel):
    c5_xlarge: float = 0.17
    c5_2xlarge: float = 0.34
    c5_4xlarge: float = 0.68
    c5_9xlarge: float = 1.53

class ScenarioParams(BaseModel):
    traffic_growth: float = 1.0
    cpu_threshold: float = 80.0
    memory_threshold: float = 85.0
    latency_target: float = 250.0
    availability_target: float = 99.9
    pricing: PricingOverride = PricingOverride()

class ExperimentRunPayload(BaseModel):
    name: str
    description: Optional[str] = None
    dataset_id: Optional[uuid.UUID] = None
    time_window_hours: int = 168
    current_instance_type: str = "c5.4xlarge"
    instance_count: int = 1
    params: ScenarioParams = ScenarioParams()

@router.post("/run-scenarios", response_model=ExperimentOut, status_code=status.HTTP_201_CREATED)
async def run_scenario_simulations(
    payload: ExperimentRunPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Runs simulations across all three scenarios (Weekday, Live Sports, Viral Video)."""
    # 1. Load telemetry data if dataset is ready
    cpu_series = None
    memory_series = None
    latency_series = None
    
    if payload.dataset_id:
        ds_res = await db.execute(select(MetricDataset).where(MetricDataset.id == payload.dataset_id))
        dataset = ds_res.scalar_one_or_none()
        if dataset and dataset.status == "ready":
            recs_res = await db.execute(
                select(MetricRecord)
                .where(MetricRecord.dataset_id == payload.dataset_id)
                .order_by(MetricRecord.timestamp.asc())
                .limit(payload.time_window_hours * 10)
            )
            rows = recs_res.scalars().all()
            if rows:
                cpu_series = [r.cpu_utilization for r in rows if r.cpu_utilization is not None]
                memory_series = [r.memory_utilization for r in rows if r.memory_utilization is not None]
                latency_series = [r.latency_ms for r in rows if r.latency_ms is not None]

    # Map schema structures
    pricing_dict = {
        "c5.xlarge": payload.params.pricing.c5_xlarge,
        "c5.2xlarge": payload.params.pricing.c5_2xlarge,
        "c5.4xlarge": payload.params.pricing.c5_4xlarge,
        "c5.9xlarge": payload.params.pricing.c5_9xlarge,
    }

    user_adjustments = {
        "traffic_growth": payload.params.traffic_growth,
        "cpu_threshold": payload.params.cpu_threshold,
        "memory_threshold": payload.params.memory_threshold,
        "latency_target": payload.params.latency_target,
        "availability_target": payload.params.availability_target,
        "instance_pricing": pricing_dict
    }

    # Helper simulation config
    from app.schemas.simulator import SimulationConfig
    config = SimulationConfig(
        name=payload.name,
        current_instance_type=payload.current_instance_type,
        current_vcpu=16, current_memory_gb=32, current_cost_per_hour_usd=pricing_dict.get(payload.current_instance_type, 0.68),
        target_instance_type="c5.2xlarge", target_vcpu=8, target_memory_gb=16, target_cost_per_hour_usd=0.34,
        instance_count=payload.instance_count,
        time_window_hours=payload.time_window_hours
    )

    # 2. Run simulation across all scenarios
    scenario_keys = ["normal_weekday", "live_sports", "viral_video"]
    scenario_results = []
    
    for key in scenario_keys:
        res = simulate_scenario(
            scenario_key=key,
            config=config,
            user_adjustments=user_adjustments,
            cpu_series=cpu_series,
            memory_series=memory_series,
            latency_series=latency_series
        )
        scenario_results.append(res)

    # 3. Format as A/B experiment response object
    comparison_results = {
        "scenarios": scenario_results,
        "winner": scenario_results[0]["recommended_configuration"]["instance_type"],
        "note": "Scenario comparison evaluated across Normal, Live Sports, and Viral Video events."
    }

    # Save to experiments table
    experiment = Experiment(
        name=payload.name,
        description=payload.description,
        dataset_id=payload.dataset_id,
        scenarios=[{"name": k, "config": user_adjustments} for k in scenario_keys],
        comparison_results=comparison_results,
        status="completed",
        created_by=current_user.id
    )
    db.add(experiment)
    await db.commit()
    await db.refresh(experiment)
    return experiment

@router.get("/", response_model=ExperimentList)
async def list_experiments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_result = await db.execute(select(func.count()).select_from(Experiment))
    total = total_result.scalar_one()
    result = await db.execute(
        select(Experiment).order_by(Experiment.created_at.desc()).offset(skip).limit(limit)
    )
    items = result.scalars().all()
    return ExperimentList(total=total, items=list(items))

@router.get("/{experiment_id}", response_model=ExperimentOut)
async def get_experiment(
    experiment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Experiment).where(Experiment.id == experiment_id))
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp

@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experiment(
    experiment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Experiment).where(Experiment.id == experiment_id))
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    await db.delete(exp)
    await db.commit()
