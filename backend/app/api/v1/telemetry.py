from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import uuid

from app.core.database import AsyncSession, get_db
from app.models.metric import MetricDataset, MetricRecord
from app.schemas.telemetry import TelemetryIngestRequest, TelemetryIngestResponse

router = APIRouter()

@router.post("/stream", response_model=TelemetryIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_telemetry_stream(
    payload: TelemetryIngestRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    High-throughput telemetry ingestion endpoint for streaming video metrics.
    In a real system, this might push to Kafka, but here we write directly to DB
    for demonstration. We create a dynamic 'Streaming' dataset if none exists.
    """
    if not payload.events:
        return TelemetryIngestResponse(status="empty", processed=0)
        
    # Find or create a default dataset for streaming
    from sqlalchemy import select
    res = await db.execute(select(MetricDataset).where(MetricDataset.name == "Live Streaming Data"))
    dataset = res.scalar_one_or_none()
    
    if not dataset:
        dataset = MetricDataset(
            name="Live Streaming Data",
            description="Dynamically ingested metrics from workload generator.",
            file_path="streamed",
            status="ready"
        )
        db.add(dataset)
        await db.flush()
        
    new_records = []
    for event in payload.events:
        record = MetricRecord(
            dataset_id=dataset.id,
            timestamp=event.timestamp,
            cpu_utilization=event.cpu_utilization,
            memory_utilization=event.memory_utilization,
            latency_ms=event.latency_ms,
            request_volume=event.request_volume,
            error_rate_pct=event.error_rate_pct,
            availability=event.availability,
            instance_count=event.instance_count,
            instance_type=event.instance_type,
            instance_price=event.instance_price
        )
        new_records.append(record)
        
    dataset.row_count += len(new_records)
    db.add_all(new_records)
    await db.commit()
    
    return TelemetryIngestResponse(status="success", processed=len(new_records))
