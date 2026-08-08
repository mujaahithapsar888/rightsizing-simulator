"""
rightsizing_engine.py
─────────────────────
Scikit-learn based rightsizing analysis engine.

Given a SimulationConfig and optionally a MetricDataset, computes:
  1. Statistical analysis of actual resource utilization
  2. CPU/Memory scaling factors for the target instance
  3. Performance risk assessment (breach probability via percentile analysis)
  4. Cost savings
  5. Recommendations with confidence scores
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

from app.schemas.simulator import SimulationConfig


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _pct_above(series: np.ndarray, threshold: float) -> float:
    """Return percentage of values above the threshold."""
    if len(series) == 0:
        return 0.0
    return float((series > threshold).sum() / len(series) * 100)


def _percentile_safe(series: np.ndarray, q: float) -> float:
    """Return percentile, returning 0 for empty arrays."""
    if len(series) == 0:
        return 0.0
    return float(np.percentile(series, q))


def _risk_score(breach_prob: float, safety_margin: float) -> float:
    """Compute 0–100 risk score from breach probability and safety margin."""
    raw = breach_prob * (1 - safety_margin / 100)
    return min(100.0, max(0.0, round(raw * 1.5, 1)))


def _risk_level(score: float) -> str:
    if score < 15:
        return "low"
    if score < 35:
        return "medium"
    if score < 65:
        return "high"
    return "critical"


# ─── Statistical resource analysis ────────────────────────────────────────────

def analyse_resources(
    cpu_series: np.ndarray,
    memory_series: np.ndarray,
    config: SimulationConfig,
) -> Dict[str, Any]:
    """
    Deep statistical analysis of resource utilization.
    Returns metrics used downstream by the risk engine.
    """
    cpu_scale = config.target_vcpu / config.current_vcpu
    mem_scale = config.target_memory_gb / config.current_memory_gb

    # Projected utilizations on the target instance
    cpu_projected = cpu_series / cpu_scale if cpu_scale > 0 else cpu_series
    mem_projected = memory_series / mem_scale if mem_scale > 0 else memory_series

    def _stats(arr: np.ndarray) -> Dict[str, float]:
        if len(arr) == 0:
            return {"mean": 0, "p50": 0, "p90": 0, "p95": 0, "p99": 0, "max": 0, "std": 0}
        return {
            "mean": round(float(arr.mean()), 2),
            "p50":  round(float(np.percentile(arr, 50)), 2),
            "p90":  round(float(np.percentile(arr, 90)), 2),
            "p95":  round(float(np.percentile(arr, 95)), 2),
            "p99":  round(float(np.percentile(arr, 99)), 2),
            "max":  round(float(arr.max()), 2),
            "std":  round(float(arr.std()), 2),
        }

    return {
        "current_cpu":   _stats(cpu_series),
        "current_memory": _stats(memory_series),
        "projected_cpu":  _stats(cpu_projected),
        "projected_memory": _stats(mem_projected),
        "scaling_factors": {
            "cpu_scale": round(cpu_scale, 4),
            "memory_scale": round(mem_scale, 4),
        },
    }


# ─── Trend detection ──────────────────────────────────────────────────────────

def detect_trend(series: np.ndarray) -> Dict[str, Any]:
    """
    Fit a simple linear trend to the series.
    Returns slope (pct/hour), direction, and R² goodness of fit.
    """
    if len(series) < 4:
        return {"slope_pct_per_hour": 0.0, "direction": "stable", "r2": 0.0}

    X = np.arange(len(series)).reshape(-1, 1)
    y = series.reshape(-1, 1)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LinearRegression()
    model.fit(X_scaled, y)

    y_pred = model.predict(X_scaled)
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    # Slope in terms of original units per step
    slope_per_step = float(model.coef_[0][0]) / float(scaler.scale_[0])
    # Assume each step is 1 hour (hourly data is most common)
    slope_pct_per_hour = round(slope_per_step, 4)

    if abs(slope_pct_per_hour) < 0.02:
        direction = "stable"
    elif slope_pct_per_hour > 0:
        direction = "increasing"
    else:
        direction = "decreasing"

    return {
        "slope_pct_per_hour": slope_pct_per_hour,
        "direction": direction,
        "r2": round(r2, 4),
    }


# ─── Risk engine ──────────────────────────────────────────────────────────────

def compute_risk(
    cpu_series: np.ndarray,
    memory_series: np.ndarray,
    config: SimulationConfig,
    resource_analysis: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compute performance risk of migrating from current → target instance.

    Risk is driven by:
      - P99 projected CPU vs. threshold
      - P99 projected memory vs. threshold
      - Trend slope (increasing workload = higher risk)
    """
    cpu_scale = config.target_vcpu / max(config.current_vcpu, 1)
    mem_scale = config.target_memory_gb / max(config.current_memory_gb, 0.5)

    # Projected utilization on target
    cpu_proj = cpu_series / cpu_scale if len(cpu_series) > 0 else np.array([0.0])
    mem_proj = memory_series / mem_scale if len(memory_series) > 0 else np.array([0.0])

    cpu_threshold = config.max_cpu_threshold_pct
    mem_threshold = config.max_memory_threshold_pct

    # Effective threshold accounting for safety margin
    effective_cpu_threshold = cpu_threshold * (1 - config.safety_margin_pct / 200)
    effective_mem_threshold = mem_threshold * (1 - config.safety_margin_pct / 200)

    cpu_breach_pct = _pct_above(cpu_proj, effective_cpu_threshold)
    mem_breach_pct = _pct_above(mem_proj, effective_mem_threshold)
    combined_breach = max(cpu_breach_pct, mem_breach_pct)

    # Trend penalty
    cpu_trend = detect_trend(cpu_series)
    mem_trend = detect_trend(memory_series)
    trend_penalty = max(
        max(0, cpu_trend["slope_pct_per_hour"] * 10),
        max(0, mem_trend["slope_pct_per_hour"] * 10),
    )

    breach_probability = min(100.0, combined_breach + trend_penalty)
    score = _risk_score(breach_probability, config.safety_margin_pct)
    level = _risk_level(score)

    affected: List[str] = []
    if cpu_breach_pct > 1:
        affected.append(f"CPU (projected p99: {resource_analysis['projected_cpu']['p99']:.1f}%)")
    if mem_breach_pct > 1:
        affected.append(f"Memory (projected p99: {resource_analysis['projected_memory']['p99']:.1f}%)")
    if cpu_trend["direction"] == "increasing":
        affected.append("CPU trend: increasing workload detected")
    if mem_trend["direction"] == "increasing":
        affected.append("Memory trend: increasing workload detected")

    recommendations = _generate_recommendations(
        level, cpu_breach_pct, mem_breach_pct,
        config, resource_analysis, cpu_trend, mem_trend,
    )

    return {
        "risk_level": level,
        "risk_score": score,
        "breach_probability_pct": round(breach_probability, 1),
        "cpu_breach_probability_pct": round(cpu_breach_pct, 1),
        "memory_breach_probability_pct": round(mem_breach_pct, 1),
        "affected_metrics": affected,
        "cpu_trend": cpu_trend,
        "memory_trend": mem_trend,
        "recommendations": recommendations,
    }


# ─── Recommendation generator ─────────────────────────────────────────────────

def _generate_recommendations(
    risk_level: str,
    cpu_breach_pct: float,
    mem_breach_pct: float,
    config: SimulationConfig,
    resource_analysis: Dict[str, Any],
    cpu_trend: Dict,
    mem_trend: Dict,
) -> List[str]:
    recs: List[str] = []

    cpu_p95 = resource_analysis["projected_cpu"]["p95"]
    mem_p95 = resource_analysis["projected_memory"]["p95"]
    cpu_mean = resource_analysis["current_cpu"]["mean"]
    mem_mean = resource_analysis["current_memory"]["mean"]

    if risk_level == "low":
        recs.append(
            f"✓ Safe to rightsize: projected CPU p95 is {cpu_p95:.1f}% "
            f"(threshold: {config.max_cpu_threshold_pct:.0f}%)"
        )
        recs.append(
            "Deploy to 10% of traffic first and monitor for 24 hours before full rollout."
        )
    elif risk_level == "medium":
        recs.append(
            f"⚠ Moderate risk: CPU breaches threshold in {cpu_breach_pct:.1f}% of periods. "
            "Use gradual canary deployment."
        )
        if cpu_p95 > config.max_cpu_threshold_pct * 0.85:
            recs.append(
                f"CPU p95 ({cpu_p95:.1f}%) is approaching the {config.max_cpu_threshold_pct:.0f}% "
                "threshold — set up auto-scaling before migration."
            )
    elif risk_level in ("high", "critical"):
        recs.append(
            f"✗ High risk: CPU/Memory may breach thresholds in {max(cpu_breach_pct, mem_breach_pct):.1f}% "
            "of periods. Consider a larger target instance."
        )
        recs.append(
            "Rightsize during off-peak hours only and ensure an immediate rollback plan is in place."
        )

    # Trend-specific recommendations
    if cpu_trend["direction"] == "increasing" and cpu_trend["r2"] > 0.5:
        recs.append(
            f"CPU is growing at ~{abs(cpu_trend['slope_pct_per_hour']):.2f}%/hr. "
            "Factor workload growth into instance selection."
        )
    if mem_trend["direction"] == "increasing" and mem_trend["r2"] > 0.5:
        recs.append(
            f"Memory is growing at ~{abs(mem_trend['slope_pct_per_hour']):.2f}%/hr. "
            "Check for memory leaks before downsizing."
        )

    # Always: latency / streaming specific advice
    recs.append(
        f"Current mean utilization: CPU {cpu_mean:.1f}%, Memory {mem_mean:.1f}%. "
        "Schedule migration during the lowest-utilization window."
    )
    recs.append(
        "Enable CloudWatch/Prometheus alerts at 70% of new instance capacity "
        "to detect headroom exhaustion early."
    )

    return recs[:6]  # cap at 6 recommendations


# ─── Cost analysis ────────────────────────────────────────────────────────────

def compute_cost_savings(config: SimulationConfig) -> Dict[str, Any]:
    """Compute monthly and annual cost savings from the instance downsize."""
    current_monthly = config.current_cost_per_hour_usd * 24 * 30 * config.instance_count
    target_monthly  = config.target_cost_per_hour_usd  * 24 * 30 * config.instance_count
    savings_monthly = current_monthly - target_monthly
    savings_annual  = savings_monthly * 12
    savings_pct     = (savings_monthly / current_monthly * 100) if current_monthly > 0 else 0.0
    roi_months      = abs(current_monthly / savings_monthly) if savings_monthly != 0 else float("inf")

    return {
        "current_monthly_cost_usd":  round(current_monthly, 2),
        "target_monthly_cost_usd":   round(target_monthly, 2),
        "monthly_savings_usd":       round(savings_monthly, 2),
        "annual_savings_usd":        round(savings_annual, 2),
        "savings_pct":               round(savings_pct, 1),
        "roi_months":                round(roi_months, 1) if not math.isinf(roi_months) else None,
        "total_instances":           config.instance_count,
    }


# ─── Top-level entry point ────────────────────────────────────────────────────

def run_rightsizing_analysis(
    config: SimulationConfig,
    cpu_series: Optional[List[float]] = None,
    memory_series: Optional[List[float]] = None,
    timestamps: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Main entry point for the rightsizing engine.

    If cpu_series / memory_series are provided (from uploaded dataset),
    the analysis is data-driven. Otherwise, conservative defaults are used.
    """
    # Convert to numpy
    cpu_arr = np.array(cpu_series, dtype=float) if cpu_series else np.array([])
    mem_arr = np.array(memory_series, dtype=float) if memory_series else np.array([])

    # If no real data, synthesise a conservative distribution
    if len(cpu_arr) == 0:
        rng = np.random.default_rng(42)
        # Simulate typical streaming cluster utilization
        hours = config.time_window_hours
        cpu_arr = np.clip(rng.normal(loc=55, scale=18, size=hours), 5, 95)
        mem_arr = np.clip(rng.normal(loc=62, scale=12, size=hours), 10, 95)

    # Remove NaN / inf
    cpu_arr = cpu_arr[np.isfinite(cpu_arr)]
    mem_arr = mem_arr[np.isfinite(mem_arr)]

    resource_analysis = analyse_resources(cpu_arr, mem_arr, config)
    cost_savings      = compute_cost_savings(config)
    risk              = compute_risk(cpu_arr, mem_arr, config, resource_analysis)

    # Compute headroom on target
    proj_cpu = resource_analysis["projected_cpu"]
    proj_mem = resource_analysis["projected_memory"]
    cpu_headroom = max(0.0, config.max_cpu_threshold_pct - proj_cpu["p95"])
    mem_headroom = max(0.0, config.max_memory_threshold_pct - proj_mem["p95"])

    # Recommendation verdict
    if risk["risk_level"] == "low":
        verdict = "safe_to_rightsize"
    elif risk["risk_level"] == "medium":
        verdict = "proceed_with_caution"
    else:
        verdict = "not_recommended"

    return {
        "cost_savings":      cost_savings,
        "performance_risk":  risk,
        "resource_analysis": {
            **resource_analysis,
            "cpu_headroom_pct":    round(cpu_headroom, 2),
            "memory_headroom_pct": round(mem_headroom, 2),
            "recommendation":      verdict,
            "data_points_analysed": len(cpu_arr),
        },
        "data_driven": len(cpu_series or []) > 0,
    }
