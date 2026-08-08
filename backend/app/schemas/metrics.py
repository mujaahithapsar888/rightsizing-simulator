from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


# ─── Dataset schemas ──────────────────────────────────────────────────────────

class MetricDatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None


class MetricDatasetOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    file_path: str
    row_count: int
    raw_row_count: int
    duplicate_count: int
    missing_value_count: int
    status: str
    error_message: Optional[str]
    validation_report: Optional[Dict[str, Any]]
    # Summary statistics
    avg_cpu_utilization: Optional[float]
    avg_memory_utilization: Optional[float]
    avg_latency_ms: Optional[float]
    avg_cost_per_hour: Optional[float]
    avg_request_volume: Optional[float]
    avg_error_rate_pct: Optional[float]
    avg_availability: Optional[float]
    # Time range
    ts_min: Optional[datetime]
    ts_max: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class MetricDatasetList(BaseModel):
    total: int
    items: List[MetricDatasetOut]


# ─── Record schemas ───────────────────────────────────────────────────────────

class MetricRecordOut(BaseModel):
    id: UUID
    dataset_id: UUID
    timestamp: datetime
    cpu_utilization: Optional[float]
    memory_utilization: Optional[float]
    latency_ms: Optional[float]
    request_volume: Optional[float]
    error_rate_pct: Optional[float]
    availability: Optional[float]
    instance_count: Optional[int]
    instance_type: Optional[str]
    instance_price: Optional[float]

    model_config = {"from_attributes": True}


class MetricRecordList(BaseModel):
    total: int
    items: List[MetricRecordOut]


# ─── Upload / validation schemas ──────────────────────────────────────────────

class ColumnValidation(BaseModel):
    column: str
    required: bool
    present: bool
    missing_count: int
    missing_pct: float


class ValidationReport(BaseModel):
    raw_rows: int
    after_dedup: int
    after_missing_drop: int
    final_rows: int
    duplicates_removed: int
    rows_with_missing: int
    columns: List[ColumnValidation]
    warnings: List[str]


class UploadResponse(BaseModel):
    dataset_id: UUID
    name: str
    row_count: int
    raw_row_count: int
    duplicate_count: int
    missing_value_count: int
    status: str
    message: str
    validation_report: ValidationReport


# ─── Statistics schema ────────────────────────────────────────────────────────

class DatasetStats(BaseModel):
    dataset_id: UUID
    record_count: int
    ts_min: Optional[datetime]
    ts_max: Optional[datetime]
    avg_cpu_utilization: Optional[float]
    avg_memory_utilization: Optional[float]
    avg_latency_ms: Optional[float]
    avg_cost_per_hour: Optional[float]
    avg_request_volume: Optional[float]
    avg_error_rate_pct: Optional[float]
    avg_availability: Optional[float]
    instance_types: List[str]
