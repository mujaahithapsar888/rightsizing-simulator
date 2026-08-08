"""Add monitoring fields to metric_datasets and rebuild metric_records

Revision ID: 001_metrics_full_schema
Revises: 
Create Date: 2026-08-08 10:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "001_metrics_full_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── metric_datasets: add new columns ─────────────────────────────────────
    op.add_column("metric_datasets", sa.Column("raw_row_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("metric_datasets", sa.Column("duplicate_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("metric_datasets", sa.Column("missing_value_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("metric_datasets", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column("metric_datasets", sa.Column("validation_report", postgresql.JSON(astext_type=sa.Text()), nullable=True))

    # Summary stats
    op.add_column("metric_datasets", sa.Column("avg_cpu_utilization", sa.Float(), nullable=True))
    op.add_column("metric_datasets", sa.Column("avg_memory_utilization", sa.Float(), nullable=True))
    op.add_column("metric_datasets", sa.Column("avg_latency_ms", sa.Float(), nullable=True))
    op.add_column("metric_datasets", sa.Column("avg_cost_per_hour", sa.Float(), nullable=True))
    op.add_column("metric_datasets", sa.Column("avg_request_volume", sa.Float(), nullable=True))
    op.add_column("metric_datasets", sa.Column("avg_error_rate_pct", sa.Float(), nullable=True))
    op.add_column("metric_datasets", sa.Column("avg_availability", sa.Float(), nullable=True))
    op.add_column("metric_datasets", sa.Column("ts_min", sa.DateTime(timezone=True), nullable=True))
    op.add_column("metric_datasets", sa.Column("ts_max", sa.DateTime(timezone=True), nullable=True))

    # ── metric_records: drop old table and recreate with full schema ──────────
    # Drop old table (cascades FK constraints)
    op.drop_table("metric_records")

    op.create_table(
        "metric_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "dataset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("metric_datasets.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("cpu_utilization", sa.Float(), nullable=True),
        sa.Column("memory_utilization", sa.Float(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("request_volume", sa.Float(), nullable=True),
        sa.Column("error_rate_pct", sa.Float(), nullable=True),
        sa.Column("availability", sa.Float(), nullable=True),
        sa.Column("instance_count", sa.Integer(), nullable=True),
        sa.Column("instance_type", sa.String(64), nullable=True, index=True),
        sa.Column("instance_price", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("metric_records")

    # Re-create old metric_records schema
    op.create_table(
        "metric_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("metric_datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("instance_id", sa.String(128), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cpu_utilization", sa.Float(), nullable=True),
        sa.Column("memory_utilization", sa.Float(), nullable=True),
        sa.Column("network_in_mbps", sa.Float(), nullable=True),
        sa.Column("network_out_mbps", sa.Float(), nullable=True),
        sa.Column("disk_read_mbps", sa.Float(), nullable=True),
        sa.Column("disk_write_mbps", sa.Float(), nullable=True),
        sa.Column("request_latency_ms", sa.Float(), nullable=True),
        sa.Column("error_rate_pct", sa.Float(), nullable=True),
        sa.Column("active_streams", sa.Integer(), nullable=True),
    )

    # Remove new metric_datasets columns
    for col in [
        "raw_row_count", "duplicate_count", "missing_value_count",
        "error_message", "validation_report",
        "avg_cpu_utilization", "avg_memory_utilization", "avg_latency_ms",
        "avg_cost_per_hour", "avg_request_volume", "avg_error_rate_pct",
        "avg_availability", "ts_min", "ts_max",
    ]:
        op.drop_column("metric_datasets", col)
