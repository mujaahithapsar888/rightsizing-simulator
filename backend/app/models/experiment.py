from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Experiment(Base):
    """A/B experiment comparing multiple rightsizing scenarios."""

    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Input dataset reference
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("metric_datasets.id", ondelete="SET NULL"),
        nullable=True,
    )

    # List of scenario configs (each identical to SimulationRun.config)
    # [{"name": "Scenario A", "config": {...}}, {"name": "Scenario B", "config": {...}}]
    scenarios: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Comparison results after experiment runs
    comparison_results: Mapped[dict] = mapped_column(JSON, nullable=True)

    # draft | running | completed | failed
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Experiment id={self.id} name={self.name} status={self.status}>"
