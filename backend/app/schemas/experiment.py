from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class ScenarioConfig(BaseModel):
    """A single scenario within an experiment."""

    name: str
    description: Optional[str] = None
    config: Dict[str, Any]  # Same structure as SimulationConfig


class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    dataset_id: Optional[UUID] = None
    scenarios: List[ScenarioConfig]


class ExperimentOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    dataset_id: Optional[UUID]
    scenarios: List[Dict[str, Any]]
    comparison_results: Optional[Dict[str, Any]]
    status: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExperimentList(BaseModel):
    total: int
    items: List[ExperimentOut]
