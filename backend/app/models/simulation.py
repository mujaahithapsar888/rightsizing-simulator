from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SimulationRun(Base):
    """Records a single rightsizing simulation execution and its results."""

    __tablename__ = "simulation_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Input dataset reference
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("metric_datasets.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Configuration stored as JSON
    # {
    #   "instance_type": "c5.2xlarge",
    #   "target_cpu_pct": 60,
    #   "target_mem_pct": 70,
    #   "target_instance_type": "c5.xlarge",
    #   "safety_margin_pct": 15,
    #   "time_window_hours": 168
    # }
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Results stored as JSON (populated after run completes)
    results: Mapped[dict] = mapped_column(JSON, nullable=True)

    # queued | running | completed | failed
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<SimulationRun id={self.id} name={self.name} status={self.status}>"
