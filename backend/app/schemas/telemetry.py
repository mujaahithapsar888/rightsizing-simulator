from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class TelemetryEvent(BaseModel):
    timestamp: datetime
    instance_type: str = Field(..., max_length=64)
    cpu_utilization: float = Field(..., ge=0, le=100)
    memory_utilization: float = Field(..., ge=0, le=100)
    latency_ms: float = Field(..., ge=0)
    request_volume: float = Field(..., ge=0)
    error_rate_pct: float = Field(..., ge=0, le=100)
    availability: float = Field(..., ge=0, le=100)
    instance_count: int = Field(1, ge=1)
    instance_price: Optional[float] = None
    
class TelemetryIngestRequest(BaseModel):
    events: List[TelemetryEvent]

class TelemetryIngestResponse(BaseModel):
    status: str
    processed: int
