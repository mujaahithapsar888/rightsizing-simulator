"""
model_routes.py
────────────────
Router exposing endpoints for training, retraining, checking status, and getting evaluation metrics
of Scikit-learn Random Forest models on historical datasets.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from app.api.deps import get_current_user
from app.core.database import AsyncSession, get_db
from app.models.metric import MetricDataset, MetricRecord
from app.models.user import User
from app.services.predictor import RightsizingPredictor

router = APIRouter()

@router.post("/{dataset_id}/train", status_code=status.HTTP_200_OK)
async def train_dataset_model(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Triggers model training/retraining for a given dataset."""
    # Ensure dataset exists and is ready
    ds_result = await db.execute(
        select(MetricDataset).where(MetricDataset.id == dataset_id)
    )
    dataset = ds_result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.status != "ready":
        raise HTTPException(status_code=400, detail="Dataset must be in 'ready' status to train models.")

    # Load dataset records from DB
    rec_result = await db.execute(
        select(MetricRecord).where(MetricRecord.dataset_id == dataset_id)
    )
    records = rec_result.scalars().all()
    
    if len(records) < 10:
        raise HTTPException(status_code=400, detail="Dataset must contain at least 10 records to train model.")

    records_list = []
    for r in records:
        records_list.append({
            "timestamp": r.timestamp,
            "cpu_utilization": r.cpu_utilization,
            "memory_utilization": r.memory_utilization,
            "latency_ms": r.latency_ms,
            "availability": r.availability,
            "instance_type": r.instance_type
        })

    predictor = RightsizingPredictor(str(dataset_id))
    try:
        metrics = predictor.train(records_list)
        return {
            "status": "success",
            "message": "Models trained successfully.",
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {e}")

@router.get("/{dataset_id}/status")
async def get_model_status(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves current model status and metrics."""
    predictor = RightsizingPredictor(str(dataset_id))
    return {
        "dataset_id": dataset_id,
        "is_trained": predictor.is_trained,
        "metrics": predictor.metrics if predictor.is_trained else None
    }
