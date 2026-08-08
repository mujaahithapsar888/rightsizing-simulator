"""
metrics_service.py
──────────────────
CSV / Parquet ingestion pipeline:
  1. Read file with Pandas
  2. Validate required columns are present
  3. Parse & coerce types
  4. Detect / report missing values
  5. Remove duplicates
  6. Sort by timestamp
  7. Bulk-insert MetricRecord rows
  8. Compute and persist summary statistics on MetricDataset
"""
from __future__ import annotations

import io
import math
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.metric import MetricDataset, MetricRecord
from app.schemas.metrics import ColumnValidation, ValidationReport

# ─── Column manifest ─────────────────────────────────────────────────────────
# Maps CSV column names (case-insensitive) → (model attr, dtype, required)
COLUMN_MAP: Dict[str, Tuple[str, str, bool]] = {
    "timestamp":          ("timestamp",          "datetime", True),
    "cpu_utilization":    ("cpu_utilization",    "float",    True),
    "memory_utilization": ("memory_utilization", "float",    True),
    "latency":            ("latency_ms",         "float",    True),
    "latency_ms":         ("latency_ms",         "float",    True),
    "request_volume":     ("request_volume",     "float",    True),
    "instance_count":     ("instance_count",     "int",      True),
    "instance_type":      ("instance_type",      "str",      True),
    "instance_price":     ("instance_price",     "float",    True),
    "availability":       ("availability",       "float",    True),
    "error_rate":         ("error_rate_pct",     "float",    True),
    "error_rate_pct":     ("error_rate_pct",     "float",    True),
}

REQUIRED_CSV_COLS = {
    "timestamp", "cpu_utilization", "memory_utilization",
    "instance_count", "instance_type", "instance_price", "availability",
}
# At least one of latency aliases
LATENCY_ALIASES    = {"latency", "latency_ms"}
# At least one of request volume aliases
VOLUME_ALIASES     = {"request_volume"}
# At least one of error rate aliases
ERROR_ALIASES      = {"error_rate", "error_rate_pct"}

REQUIRED_GROUPS = [
    (LATENCY_ALIASES,    "latency / latency_ms"),
    (VOLUME_ALIASES,     "request_volume"),
    (ERROR_ALIASES,      "error_rate / error_rate_pct"),
]


def _safe_float(v: Any) -> Optional[float]:
    try:
        f = float(v)
        return None if math.isnan(f) or math.isinf(f) else f
    except Exception:
        return None


def _safe_int(v: Any) -> Optional[int]:
    try:
        return int(float(v))
    except Exception:
        return None


# ─── Main pipeline ────────────────────────────────────────────────────────────

async def ingest_csv(
    contents: bytes,
    filename: str,
    dataset: MetricDataset,
    db: AsyncSession,
) -> ValidationReport:
    """
    Parse, validate, clean, and persist metric records from raw CSV/Parquet bytes.
    Updates the dataset object with computed statistics; caller must commit.
    """
    warnings: List[str] = []

    # ── 1. Read ────────────────────────────────────────────────────────────────
    try:
        if filename.endswith(".parquet"):
            df = pd.read_parquet(io.BytesIO(contents))
        else:
            df = pd.read_csv(io.BytesIO(contents), low_memory=False)
    except Exception as exc:
        dataset.status = "error"
        dataset.error_message = f"Could not parse file: {exc}"
        raise ValueError(dataset.error_message)

    raw_rows = len(df)
    dataset.raw_row_count = raw_rows

    # Normalise column names
    df.columns = [c.strip().lower() for c in df.columns]

    # ── 2. Validate required columns ──────────────────────────────────────────
    missing_cols: List[str] = []
    for col in REQUIRED_CSV_COLS:
        if col not in df.columns:
            missing_cols.append(col)
    for aliases, label in REQUIRED_GROUPS:
        if not any(a in df.columns for a in aliases):
            missing_cols.append(label)

    if missing_cols:
        dataset.status = "error"
        dataset.error_message = f"Missing required columns: {missing_cols}"
        raise ValueError(dataset.error_message)

    # Resolve aliases to canonical names
    if "latency" in df.columns and "latency_ms" not in df.columns:
        df.rename(columns={"latency": "latency_ms"}, inplace=True)
    if "error_rate" in df.columns and "error_rate_pct" not in df.columns:
        df.rename(columns={"error_rate": "error_rate_pct"}, inplace=True)

    # ── 3. Per-column validation report ───────────────────────────────────────
    col_validations: List[ColumnValidation] = []
    all_model_cols = [
        ("timestamp",          True),
        ("cpu_utilization",    True),
        ("memory_utilization", True),
        ("latency_ms",         True),
        ("request_volume",     True),
        ("instance_count",     True),
        ("instance_type",      True),
        ("instance_price",     True),
        ("availability",       True),
        ("error_rate_pct",     True),
    ]
    for col_name, required in all_model_cols:
        present = col_name in df.columns
        if present:
            missing_n = int(df[col_name].isna().sum())
            missing_pct = round(missing_n / raw_rows * 100, 2) if raw_rows else 0.0
        else:
            missing_n = raw_rows
            missing_pct = 100.0
        col_validations.append(ColumnValidation(
            column=col_name,
            required=required,
            present=present,
            missing_count=missing_n,
            missing_pct=missing_pct,
        ))

    # ── 4. Parse timestamp ────────────────────────────────────────────────────
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    bad_ts = df["timestamp"].isna().sum()
    if bad_ts > 0:
        warnings.append(f"{bad_ts} rows had unparseable timestamps and were dropped.")
    df = df.dropna(subset=["timestamp"])

    # ── 5. Remove duplicates ──────────────────────────────────────────────────
    dedup_cols = ["timestamp", "instance_type"] if "instance_type" in df.columns else ["timestamp"]
    before_dedup = len(df)
    df = df.drop_duplicates(subset=dedup_cols)
    duplicates_removed = before_dedup - len(df)
    if duplicates_removed:
        warnings.append(f"Removed {duplicates_removed:,} duplicate rows (same timestamp + instance_type).")

    after_dedup = len(df)

    # ── 6. Detect & report missing values (don't drop — just fill with None) ──
    required_for_nullcheck = ["cpu_utilization", "memory_utilization"]
    rows_with_any_missing = int(df[required_for_nullcheck].isna().any(axis=1).sum())
    if rows_with_any_missing:
        warnings.append(
            f"{rows_with_any_missing:,} rows have missing CPU or Memory values "
            "(stored as NULL — review before simulation)."
        )

    after_missing = len(df)

    # ── 7. Sort by timestamp ──────────────────────────────────────────────────
    df = df.sort_values("timestamp").reset_index(drop=True)

    # ── 8. Bulk-insert records ────────────────────────────────────────────────
    def _get(row: pd.Series, col: str) -> Any:
        return row[col] if col in row.index else None

    batch_size = 2_000
    records_to_insert: List[MetricRecord] = []

    for _, row in df.iterrows():
        rec = MetricRecord(
            dataset_id=dataset.id,
            timestamp=row["timestamp"].to_pydatetime(),
            cpu_utilization=_safe_float(_get(row, "cpu_utilization")),
            memory_utilization=_safe_float(_get(row, "memory_utilization")),
            latency_ms=_safe_float(_get(row, "latency_ms")),
            request_volume=_safe_float(_get(row, "request_volume")),
            error_rate_pct=_safe_float(_get(row, "error_rate_pct")),
            availability=_safe_float(_get(row, "availability")),
            instance_count=_safe_int(_get(row, "instance_count")),
            instance_type=str(_get(row, "instance_type")) if _get(row, "instance_type") is not None else None,
            instance_price=_safe_float(_get(row, "instance_price")),
        )
        records_to_insert.append(rec)

        if len(records_to_insert) >= batch_size:
            db.add_all(records_to_insert)
            await db.flush()
            records_to_insert.clear()

    if records_to_insert:
        db.add_all(records_to_insert)
        await db.flush()

    final_rows = after_missing

    # ── 9. Compute summary statistics ─────────────────────────────────────────
    def _mean(col: str) -> Optional[float]:
        if col not in df.columns:
            return None
        s = df[col].dropna()
        return round(float(s.mean()), 4) if len(s) > 0 else None

    dataset.row_count = final_rows
    dataset.duplicate_count = duplicates_removed
    dataset.missing_value_count = rows_with_any_missing
    dataset.avg_cpu_utilization    = _mean("cpu_utilization")
    dataset.avg_memory_utilization = _mean("memory_utilization")
    dataset.avg_latency_ms         = _mean("latency_ms")
    dataset.avg_cost_per_hour      = _mean("instance_price")
    dataset.avg_request_volume     = _mean("request_volume")
    dataset.avg_error_rate_pct     = _mean("error_rate_pct")
    dataset.avg_availability       = _mean("availability")
    dataset.ts_min = df["timestamp"].min().to_pydatetime() if len(df) > 0 else None
    dataset.ts_max = df["timestamp"].max().to_pydatetime() if len(df) > 0 else None
    dataset.status = "ready"

    report = ValidationReport(
        raw_rows=raw_rows,
        after_dedup=after_dedup,
        after_missing_drop=after_missing,
        final_rows=final_rows,
        duplicates_removed=duplicates_removed,
        rows_with_missing=rows_with_any_missing,
        columns=col_validations,
        warnings=warnings,
    )

    dataset.validation_report = report.model_dump(mode="json")
    return report
