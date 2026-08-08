"""
experiment_engine.py
─────────────────────
A/B Experiment comparison engine.

Given N scenarios (each is a SimulationConfig-like dict + optional dataset),
the engine:
  1. Runs rightsizing_engine for each scenario
  2. Computes a composite score (savings vs risk)
  3. Ranks scenarios and produces a winner
  4. Generates a textual comparison summary
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import numpy as np

from app.schemas.simulator import SimulationConfig
from app.services.rightsizing_engine import run_rightsizing_analysis

# Preset catalog (mirrors frontend INSTANCE_PRESETS)
INSTANCE_CATALOG: Dict[str, Dict[str, float]] = {
    "c5.xlarge":  {"vcpu": 4,  "memory_gb": 8,   "cost": 0.170},
    "c5.2xlarge": {"vcpu": 8,  "memory_gb": 16,  "cost": 0.340},
    "c5.4xlarge": {"vcpu": 16, "memory_gb": 32,  "cost": 0.680},
    "c5.9xlarge": {"vcpu": 36, "memory_gb": 72,  "cost": 1.530},
    "m5.xlarge":  {"vcpu": 4,  "memory_gb": 16,  "cost": 0.192},
    "m5.2xlarge": {"vcpu": 8,  "memory_gb": 32,  "cost": 0.384},
    "m5.4xlarge": {"vcpu": 16, "memory_gb": 64,  "cost": 0.768},
    "r5.xlarge":  {"vcpu": 4,  "memory_gb": 32,  "cost": 0.252},
    "r5.2xlarge": {"vcpu": 8,  "memory_gb": 64,  "cost": 0.504},
}


def _lookup(instance_type: str, field: str, default: float) -> float:
    return INSTANCE_CATALOG.get(instance_type, {}).get(field, default)


def _composite_score(monthly_savings: float, risk_score: float, weight_savings: float = 0.6) -> float:
    """
    Blend savings (higher = better) and risk (lower = better) into a 0–100 score.
    weight_savings controls the savings vs safety trade-off.
    """
    max_savings = 10_000  # normalise against $10k/mo
    savings_norm = min(monthly_savings / max_savings * 100, 100)
    safety_norm  = max(0, 100 - risk_score)
    return round(savings_norm * weight_savings + safety_norm * (1 - weight_savings), 2)


def _verdict(risk_level: str) -> str:
    return {
        "low":      "safe_to_rightsize",
        "medium":   "proceed_with_caution",
        "high":     "not_recommended",
        "critical": "do_not_rightsize",
    }.get(risk_level, "evaluate")


def run_experiment(
    scenarios: List[Dict[str, Any]],
    dataset_cpu: Optional[List[float]] = None,
    dataset_memory: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Compare N rightsizing scenarios.

    Each scenario dict must have at minimum:
      current_instance_type, target_instance_type,
      (optional) safety_margin_pct, instance_count, time_window_hours

    Returns a structured comparison_results dict suitable for JSON storage.
    """
    results: List[Dict[str, Any]] = []

    for scenario in scenarios:
        cfg_dict = scenario.get("config", scenario)
        current_type = cfg_dict.get("current_instance_type", "c5.4xlarge")
        target_type  = cfg_dict.get("target_instance_type",  "c5.2xlarge")

        sim_config = SimulationConfig(
            name=scenario.get("name", "Scenario"),
            current_instance_type=current_type,
            current_vcpu=int(_lookup(current_type, "vcpu", 16)),
            current_memory_gb=_lookup(current_type, "memory_gb", 32),
            current_cost_per_hour_usd=cfg_dict.get(
                "current_cost_per_hour_usd", _lookup(current_type, "cost", 0.68)
            ),
            target_instance_type=target_type,
            target_vcpu=int(_lookup(target_type, "vcpu", 8)),
            target_memory_gb=_lookup(target_type, "memory_gb", 16),
            target_cost_per_hour_usd=cfg_dict.get(
                "target_cost_per_hour_usd", _lookup(target_type, "cost", 0.34)
            ),
            max_cpu_threshold_pct=float(cfg_dict.get("max_cpu_threshold_pct", 80)),
            max_memory_threshold_pct=float(cfg_dict.get("max_memory_threshold_pct", 85)),
            safety_margin_pct=float(cfg_dict.get("safety_margin_pct", 15)),
            time_window_hours=int(cfg_dict.get("time_window_hours", 168)),
            instance_count=int(cfg_dict.get("instance_count", 1)),
        )

        analysis = run_rightsizing_analysis(
            config=sim_config,
            cpu_series=dataset_cpu,
            memory_series=dataset_memory,
        )

        cost   = analysis["cost_savings"]
        risk   = analysis["performance_risk"]
        res_an = analysis["resource_analysis"]

        score = _composite_score(cost["monthly_savings_usd"], risk["risk_score"])

        results.append({
            "name":                         scenario.get("name", "Scenario"),
            "current_instance_type":        current_type,
            "target_instance_type":         target_type,
            "instance_count":               sim_config.instance_count,
            # Cost
            "current_monthly_cost_usd":     cost["current_monthly_cost_usd"],
            "target_monthly_cost_usd":      cost["target_monthly_cost_usd"],
            "monthly_savings_usd":          cost["monthly_savings_usd"],
            "annual_savings_usd":           cost["annual_savings_usd"],
            "savings_pct":                  cost["savings_pct"],
            "roi_months":                   cost.get("roi_months"),
            # Risk
            "risk_level":                   risk["risk_level"],
            "risk_score":                   risk["risk_score"],
            "breach_probability_pct":       risk["breach_probability_pct"],
            "cpu_breach_pct":               risk["cpu_breach_probability_pct"],
            "memory_breach_pct":            risk["memory_breach_probability_pct"],
            "cpu_trend":                    risk.get("cpu_trend", {}),
            "memory_trend":                 risk.get("memory_trend", {}),
            # Resource headroom
            "cpu_headroom_pct":             res_an.get("cpu_headroom_pct", 0),
            "memory_headroom_pct":          res_an.get("memory_headroom_pct", 0),
            "projected_cpu_p95":            res_an.get("projected_cpu", {}).get("p95", 0),
            "projected_memory_p95":         res_an.get("projected_memory", {}).get("p95", 0),
            "data_points_analysed":         res_an.get("data_points_analysed", 0),
            # Scores
            "composite_score":              score,
            "recommendation":               _verdict(risk["risk_level"]),
            "recommendations":              risk.get("recommendations", []),
            "data_driven":                  analysis.get("data_driven", False),
        })

    # Rank by composite score (highest = best)
    ranked = sorted(results, key=lambda r: r["composite_score"], reverse=True)
    winner = ranked[0]["name"] if ranked else None

    # Determine best for cost, best for safety
    best_savings = max(results, key=lambda r: r["monthly_savings_usd"])["name"] if results else None
    best_safety  = min(results, key=lambda r: r["risk_score"])["name"] if results else None

    # Executive summary
    total_savings  = sum(r["monthly_savings_usd"] for r in results)
    risk_levels    = [r["risk_level"] for r in results]
    n_safe         = sum(1 for rl in risk_levels if rl == "low")
    summary_lines  = [
        f"Compared {len(results)} scenarios across {results[0].get('data_points_analysed', 0):,} data points.",
        f"Winner by composite score: {winner}.",
        f"Best cost savings: {best_savings} (${max(r['monthly_savings_usd'] for r in results):,.2f}/mo).",
        f"Lowest risk: {best_safety}.",
        f"{n_safe}/{len(results)} scenarios rated low-risk.",
    ]

    return {
        "scenarios":      ranked,
        "winner":         winner,
        "best_savings":   best_savings,
        "best_safety":    best_safety,
        "summary":        " ".join(summary_lines),
        "data_driven":    any(r["data_driven"] for r in results),
        "total_scenarios": len(results),
    }
