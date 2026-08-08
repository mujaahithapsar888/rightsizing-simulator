from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class ReportCreate(BaseModel):
    title: str
    report_type: str = "simulation_summary"
    simulation_id: Optional[UUID] = None
    experiment_id: Optional[UUID] = None


class ReportOut(BaseModel):
    id: UUID
    title: str
    report_type: str
    simulation_id: Optional[UUID]
    experiment_id: Optional[UUID]
    content: Dict[str, Any]
    rendered_content: Optional[str]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportList(BaseModel):
    total: int
    items: List[ReportOut]
