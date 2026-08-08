from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SimulationConfig(BaseModel):
    """Configuration inputs for a rightsizing simulation."""

    name: str = Field(..., description="Human-readable name for this simulation run")
    description: Optional[str] = None
    dataset_id: Optional[UUID] = None

    # Current instance spec
    current_instance_type: str = Field(..., example="c5.4xlarge")
    current_vcpu: int = Field(..., ge=1, example=16)
    current_memory_gb: float = Field(..., ge=0.5, example=32.0)
    current_cost_per_hour_usd: float = Field(..., ge=0, example=0.68)

    # Target instance spec
    target_instance_type: str = Field(..., example="c5.2xlarge")
    target_vcpu: int = Field(..., ge=1, example=8)
    target_memory_gb: float = Field(..., ge=0.5, example=16.0)
    target_cost_per_hour_usd: float = Field(..., ge=0, example=0.34)

    # Safety thresholds
    max_cpu_threshold_pct: float = Field(default=80.0, ge=0, le=100)
    max_memory_threshold_pct: float = Field(default=85.0, ge=0, le=100)
    safety_margin_pct: float = Field(default=15.0, ge=0, le=50)

    # Time window for analysis (hours)
    time_window_hours: int = Field(default=168, ge=1, description="Analysis window in hours (168 = 1 week)")

    # Number of instances to rightsize
    instance_count: int = Field(default=1, ge=1)


class CostSavings(BaseModel):
    current_monthly_cost_usd: float
    target_monthly_cost_usd: float
    monthly_savings_usd: float
    annual_savings_usd: float
    savings_pct: float


class PerformanceRisk(BaseModel):
    risk_level: str  # low | medium | high | critical
    risk_score: float  # 0–100
    breach_probability_pct: float
    affected_metrics: List[str]
    recommendations: List[str]


class SimulationResultOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    dataset_id: Optional[UUID]
    config: Dict[str, Any]
    results: Optional[Dict[str, Any]]
    status: str
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class SimulationRunList(BaseModel):
    total: int
    items: List[SimulationResultOut]
