from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MetricDataset(Base):
    """Represents an uploaded CSV file / batch of metrics."""

    __tablename__ = "metric_datasets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # Row counts
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    raw_row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    missing_value_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Status: pending | processing | ready | error
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    # Validation report stored as JSON
    validation_report: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Precomputed summary statistics
    avg_cpu_utilization: Mapped[float] = mapped_column(Float, nullable=True)
    avg_memory_utilization: Mapped[float] = mapped_column(Float, nullable=True)
    avg_latency_ms: Mapped[float] = mapped_column(Float, nullable=True)
    avg_cost_per_hour: Mapped[float] = mapped_column(Float, nullable=True)
    avg_request_volume: Mapped[float] = mapped_column(Float, nullable=True)
    avg_error_rate_pct: Mapped[float] = mapped_column(Float, nullable=True)
    avg_availability: Mapped[float] = mapped_column(Float, nullable=True)

    # Time range
    ts_min: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    ts_max: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    records: Mapped[list["MetricRecord"]] = relationship(
        "MetricRecord", back_populates="dataset", cascade="all, delete-orphan", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<MetricDataset id={self.id} name={self.name} rows={self.row_count}>"


class MetricRecord(Base):
    """Individual time-series metric sample parsed from an uploaded CSV."""

    __tablename__ = "metric_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("metric_datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ─── Required columns ─────────────────────────────────────────────────────
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # ─── Resource utilization (0–100 %) ───────────────────────────────────────
    cpu_utilization: Mapped[float] = mapped_column(Float, nullable=True)
    memory_utilization: Mapped[float] = mapped_column(Float, nullable=True)

    # ─── Performance ──────────────────────────────────────────────────────────
    latency_ms: Mapped[float] = mapped_column(Float, nullable=True)
    request_volume: Mapped[float] = mapped_column(Float, nullable=True)
    error_rate_pct: Mapped[float] = mapped_column(Float, nullable=True)
    availability: Mapped[float] = mapped_column(Float, nullable=True)

    # ─── Infrastructure ───────────────────────────────────────────────────────
    instance_count: Mapped[int] = mapped_column(Integer, nullable=True)
    instance_type: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    instance_price: Mapped[float] = mapped_column(Float, nullable=True)

    dataset: Mapped["MetricDataset"] = relationship("MetricDataset", back_populates="records")

    def __repr__(self) -> str:
        return f"<MetricRecord id={self.id} ts={self.timestamp} type={self.instance_type}>"
