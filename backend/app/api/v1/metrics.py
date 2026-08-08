"""
metrics.py — Metrics API Router
────────────────────────────────
Endpoints:
  POST  /upload            Upload & process a CSV/Parquet file
  GET   /                  List all datasets (paginated)
  GET   /{id}              Get single dataset metadata
  GET   /{id}/records      Get paginated records with search
  GET   /{id}/stats        Get computed summary statistics
  DELETE /{id}             Delete dataset + file + all records
"""
from __future__ import annotations

import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, or_, select

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import AsyncSession, get_db
from app.models.metric import MetricDataset, MetricRecord
from app.models.user import User
from app.schemas.metrics import (
    DatasetStats,
    MetricDatasetList,
    MetricDatasetOut,
    MetricRecordList,
    MetricRecordOut,
    UploadResponse,
)
from app.services.metrics_service import ingest_csv

router = APIRouter()

ALLOWED_EXTENSIONS = {".csv", ".parquet"}


# ─── POST /upload ─────────────────────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_metrics(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a CSV or Parquet file of historical monitoring metrics.

    The pipeline will:
    - Validate required columns are present
    - Report missing values per column
    - Remove duplicate rows (same timestamp + instance_type)
    - Sort all rows by timestamp ascending
    - Bulk-insert cleaned records into PostgreSQL
    - Compute and persist summary statistics
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    contents = await file.read()
    if len(contents) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_size_mb} MB limit",
        )

    # Save raw file to disk
    os.makedirs(settings.upload_dir, exist_ok=True)
    file_id = str(uuid.uuid4())
    dest_path = os.path.join(settings.upload_dir, f"{file_id}{ext}")
    with open(dest_path, "wb") as fh:
        fh.write(contents)

    # Create dataset record (status=processing)
    dataset = MetricDataset(
        name=name,
        description=description,
        file_path=dest_path,
        status="processing",
        uploaded_by=current_user.id,
    )
    db.add(dataset)
    await db.flush()  # get the ID before ingestion

    try:
        validation_report = await ingest_csv(contents, file.filename or "", dataset, db)
    except ValueError as exc:
        await db.rollback()
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        await db.rollback()
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {exc}",
        )

    await db.commit()
    await db.refresh(dataset)

    return UploadResponse(
        dataset_id=dataset.id,
        name=dataset.name,
        row_count=dataset.row_count,
        raw_row_count=dataset.raw_row_count,
        duplicate_count=dataset.duplicate_count,
        missing_value_count=dataset.missing_value_count,
        status=dataset.status,
        message=(
            f"✓ Imported {dataset.row_count:,} records "
            f"({dataset.duplicate_count:,} duplicates removed, "
            f"{dataset.missing_value_count:,} rows with missing values flagged)"
        ),
        validation_report=validation_report,
    )


# ─── GET / ────────────────────────────────────────────────────────────────────

@router.get("/", response_model=MetricDatasetList)
async def list_datasets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all uploaded metric datasets, newest first."""
    total_result = await db.execute(select(func.count()).select_from(MetricDataset))
    total = total_result.scalar_one()

    result = await db.execute(
        select(MetricDataset)
        .order_by(MetricDataset.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    items = result.scalars().all()
    return MetricDatasetList(total=total, items=list(items))


# ─── GET /{id} ────────────────────────────────────────────────────────────────

@router.get("/{dataset_id}", response_model=MetricDatasetOut)
async def get_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(MetricDataset).where(MetricDataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


# ─── GET /{id}/records ───────────────────────────────────────────────────────

@router.get("/{dataset_id}/records", response_model=MetricRecordList)
async def list_records(
    dataset_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None, description="Filter by instance_type (partial match)"),
    instance_type: Optional[str] = Query(None, description="Filter by exact instance_type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return paginated metric records for a dataset with optional search/filter."""
    # Ensure dataset exists
    ds_result = await db.execute(select(MetricDataset).where(MetricDataset.id == dataset_id))
    if not ds_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Dataset not found")

    base_q = select(MetricRecord).where(MetricRecord.dataset_id == dataset_id)

    if instance_type:
        base_q = base_q.where(MetricRecord.instance_type == instance_type)
    elif search:
        base_q = base_q.where(MetricRecord.instance_type.ilike(f"%{search}%"))

    count_q = select(func.count()).select_from(base_q.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar_one()

    result = await db.execute(
        base_q.order_by(MetricRecord.timestamp.asc()).offset(skip).limit(limit)
    )
    items = result.scalars().all()
    return MetricRecordList(total=total, items=list(items))


# ─── GET /{id}/stats ─────────────────────────────────────────────────────────

@router.get("/{dataset_id}/stats", response_model=DatasetStats)
async def get_dataset_stats(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return pre-computed summary statistics for a dataset."""
    result = await db.execute(select(MetricDataset).where(MetricDataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Distinct instance types from records
    it_result = await db.execute(
        select(MetricRecord.instance_type)
        .where(MetricRecord.dataset_id == dataset_id)
        .distinct()
    )
    instance_types = [r for (r,) in it_result.all() if r is not None]

    return DatasetStats(
        dataset_id=dataset_id,
        record_count=dataset.row_count,
        ts_min=dataset.ts_min,
        ts_max=dataset.ts_max,
        avg_cpu_utilization=dataset.avg_cpu_utilization,
        avg_memory_utilization=dataset.avg_memory_utilization,
        avg_latency_ms=dataset.avg_latency_ms,
        avg_cost_per_hour=dataset.avg_cost_per_hour,
        avg_request_volume=dataset.avg_request_volume,
        avg_error_rate_pct=dataset.avg_error_rate_pct,
        avg_availability=dataset.avg_availability,
        instance_types=instance_types,
    )


# ─── DELETE /{id} ────────────────────────────────────────────────────────────

@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a dataset, its file on disk, and all associated metric records."""
    result = await db.execute(select(MetricDataset).where(MetricDataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Remove file from disk
    if os.path.exists(dataset.file_path):
        os.remove(dataset.file_path)

    await db.delete(dataset)  # cascades to metric_records
    await db.commit()
