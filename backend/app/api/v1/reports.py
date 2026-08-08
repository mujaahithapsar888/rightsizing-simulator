"""
reports.py — Reports API Router with Benchmarks
─────────────────────────────────────────────────
Integrates with the benchmarker engine. Exposes endpoints to trigger
automated benchmarking comparing Baseline vs Optimized.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from app.api.deps import get_current_user
from app.core.database import AsyncSession, get_db
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportList, ReportOut
from app.services.benchmarker import run_automated_benchmark

router = APIRouter()

class BenchmarkPayload(BaseModel):
    title: str
    current_instance_type: str = "c5.4xlarge"

@router.post("/benchmark", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
async def run_benchmark_simulation(
    payload: BenchmarkPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Runs automated benchmark tests and stores results as a performance report."""
    results = run_automated_benchmark(payload.current_instance_type)
    
    report = Report(
        title=payload.title,
        report_type="cost_analysis", # maps to cost_analysis rendering template
        simulation_id=None,
        experiment_id=None,
        content=results,
        rendered_content=None,
        status="final",
        created_by=current_user.id
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report

@router.get("/", response_model=ReportList)
async def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_result = await db.execute(select(func.count()).select_from(Report))
    total = total_result.scalar_one()
    result = await db.execute(
        select(Report).order_by(Report.created_at.desc()).offset(skip).limit(limit)
    )
    items = result.scalars().all()
    return ReportList(total=total, items=list(items))

@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    return report

@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    await db.delete(report)
    await db.commit()
