"""
report_generator.py
────────────────────
Builds rich, structured JSON report content from simulation / experiment data.
Includes executive summary, cost tables, risk breakdown, and recommendations.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _fmt_usd(v: float) -> str:
    return f"${v:,.2f}"


def _fmt_pct(v: float) -> str:
    return f"{v:.1f}%"


def _risk_emoji(level: str) -> str:
    return {"low": "✓", "medium": "⚠", "high": "✗", "critical": "🚨"}.get(level, "•")


# ─── Simulation Summary ───────────────────────────────────────────────────────

def build_simulation_summary(simulation: Any) -> Dict[str, Any]:
    cfg = simulation.config or {}
    res = simulation.results or {}

    cost   = res.get("cost_savings", {})
    risk   = res.get("performance_risk", {})
    res_an = res.get("resource_analysis", {})

    rec = res_an.get("recommendation", "evaluate")
    risk_level = risk.get("risk_level", "unknown")

    return {
        "report_type":      "simulation_summary",
        "generated_at":     datetime.now(timezone.utc).isoformat(),
        "simulation_name":  simulation.name,
        "simulation_id":    str(simulation.id),
        "status":           simulation.status,
        "data_driven":      res.get("data_driven", False),

        "configuration": {
            "current_instance":      cfg.get("current_instance_type"),
            "target_instance":       cfg.get("target_instance_type"),
            "current_vcpu":          cfg.get("current_vcpu"),
            "target_vcpu":           cfg.get("target_vcpu"),
            "current_memory_gb":     cfg.get("current_memory_gb"),
            "target_memory_gb":      cfg.get("target_memory_gb"),
            "instance_count":        cfg.get("instance_count", 1),
            "time_window_hours":     cfg.get("time_window_hours", 168),
            "cpu_threshold_pct":     cfg.get("max_cpu_threshold_pct", 80),
            "memory_threshold_pct":  cfg.get("max_memory_threshold_pct", 85),
            "safety_margin_pct":     cfg.get("safety_margin_pct", 15),
        },

        "cost_analysis": {
            "current_monthly_usd":   cost.get("current_monthly_cost_usd", 0),
            "target_monthly_usd":    cost.get("target_monthly_cost_usd", 0),
            "monthly_savings_usd":   cost.get("monthly_savings_usd", 0),
            "annual_savings_usd":    cost.get("annual_savings_usd", 0),
            "savings_pct":           cost.get("savings_pct", 0),
            "roi_months":            cost.get("roi_months"),
            "total_instances":       cost.get("total_instances", 1),
            # Formatted versions for display
            "current_monthly_fmt":   _fmt_usd(cost.get("current_monthly_cost_usd", 0)),
            "target_monthly_fmt":    _fmt_usd(cost.get("target_monthly_cost_usd", 0)),
            "monthly_savings_fmt":   _fmt_usd(cost.get("monthly_savings_usd", 0)),
            "annual_savings_fmt":    _fmt_usd(cost.get("annual_savings_usd", 0)),
        },

        "risk_assessment": {
            "risk_level":                risk_level,
            "risk_score":                risk.get("risk_score", 0),
            "breach_probability_pct":    risk.get("breach_probability_pct", 0),
            "cpu_breach_pct":            risk.get("cpu_breach_probability_pct", 0),
            "memory_breach_pct":         risk.get("memory_breach_probability_pct", 0),
            "verdict_emoji":             _risk_emoji(risk_level),
            "affected_metrics":          risk.get("affected_metrics", []),
        },

        "resource_analysis": {
            "cpu_headroom_pct":          res_an.get("cpu_headroom_pct", 0),
            "memory_headroom_pct":       res_an.get("memory_headroom_pct", 0),
            "data_points_analysed":      res_an.get("data_points_analysed", 0),
            "cpu_p95_current":           res_an.get("current_cpu", {}).get("p95"),
            "cpu_p95_projected":         res_an.get("projected_cpu", {}).get("p95"),
            "mem_p95_current":           res_an.get("current_memory", {}).get("p95"),
            "mem_p95_projected":         res_an.get("projected_memory", {}).get("p95"),
            "cpu_scaling_factor":        res_an.get("scaling_factors", {}).get("cpu_scale"),
            "memory_scaling_factor":     res_an.get("scaling_factors", {}).get("memory_scale"),
        },

        "recommendation": rec,
        "recommendations": risk.get("recommendations", []),

        "executive_summary": (
            f"Simulation '{simulation.name}' evaluated migrating "
            f"{cfg.get('instance_count', 1)}× {cfg.get('current_instance_type')} "
            f"→ {cfg.get('target_instance_type')}. "
            f"Projected monthly savings: {_fmt_usd(cost.get('monthly_savings_usd', 0))} "
            f"({_fmt_pct(cost.get('savings_pct', 0))} reduction). "
            f"Risk level: {_risk_emoji(risk_level)} {risk_level} "
            f"(score: {risk.get('risk_score', 0):.0f}/100). "
            f"Recommendation: {rec.replace('_', ' ')}."
        ),
    }


# ─── Experiment Comparison ───────────────────────────────────────────────────

def build_experiment_comparison(experiment: Any) -> Dict[str, Any]:
    cmp = experiment.comparison_results or {}
    scenarios = cmp.get("scenarios", [])
    winner = cmp.get("winner")
    best_savings = cmp.get("best_savings")
    best_safety  = cmp.get("best_safety")

    # Total potential savings across all scenarios
    max_savings = max((s.get("monthly_savings_usd", 0) for s in scenarios), default=0)

    scenario_rows = [
        {
            "rank":                     i + 1,
            "name":                     s.get("name"),
            "current_instance":         s.get("current_instance_type"),
            "target_instance":          s.get("target_instance_type"),
            "monthly_savings_fmt":      _fmt_usd(s.get("monthly_savings_usd", 0)),
            "monthly_savings_usd":      s.get("monthly_savings_usd", 0),
            "annual_savings_fmt":       _fmt_usd(s.get("annual_savings_usd", 0)),
            "savings_pct":              s.get("savings_pct", 0),
            "risk_level":               s.get("risk_level", "unknown"),
            "risk_score":               s.get("risk_score", 0),
            "composite_score":          s.get("composite_score", 0),
            "recommendation":           s.get("recommendation", "evaluate"),
            "is_winner":                s.get("name") == winner,
            "is_best_savings":          s.get("name") == best_savings,
            "is_best_safety":           s.get("name") == best_safety,
            "cpu_headroom_pct":         s.get("cpu_headroom_pct", 0),
            "memory_headroom_pct":      s.get("memory_headroom_pct", 0),
            "breach_probability_pct":   s.get("breach_probability_pct", 0),
        }
        for i, s in enumerate(scenarios)
    ]

    return {
        "report_type":      "experiment_comparison",
        "generated_at":     datetime.now(timezone.utc).isoformat(),
        "experiment_name":  experiment.name,
        "experiment_id":    str(experiment.id),
        "data_driven":      cmp.get("data_driven", False),
        "total_scenarios":  len(scenarios),

        "winner":           winner,
        "best_savings":     best_savings,
        "best_safety":      best_safety,
        "max_monthly_savings_usd": max_savings,
        "max_monthly_savings_fmt": _fmt_usd(max_savings),

        "scenarios":        scenario_rows,

        "comparison_summary": cmp.get("summary", ""),

        "executive_summary": (
            f"Experiment '{experiment.name}' compared {len(scenarios)} rightsizing scenarios. "
            f"Winner (best composite score): {winner}. "
            f"Maximum monthly savings achievable: {_fmt_usd(max_savings)}. "
            f"Best safety profile: {best_safety}. "
            f"{'Analysis used real telemetry data.' if cmp.get('data_driven') else 'Analysis used synthetic data — upload a metrics dataset for data-driven results.'}"
        ),
    }


# ─── Cost Analysis ────────────────────────────────────────────────────────────

def build_cost_analysis(simulation: Any) -> Dict[str, Any]:
    """Focused cost breakdown report."""
    base = build_simulation_summary(simulation)
    cost = base["cost_analysis"]
    cfg  = base["configuration"]

    monthly_savings = cost["monthly_savings_usd"]
    n = cfg.get("instance_count", 1) or 1

    return {
        "report_type":       "cost_analysis",
        "generated_at":      base["generated_at"],
        "simulation_name":   simulation.name,
        "simulation_id":     str(simulation.id),

        "instance_migration": {
            "from": cfg.get("current_instance"),
            "to":   cfg.get("target_instance"),
            "count": n,
        },

        "cost_breakdown": {
            "per_instance_monthly_before": _fmt_usd(cost["current_monthly_usd"] / n),
            "per_instance_monthly_after":  _fmt_usd(cost["target_monthly_usd"] / n),
            "per_instance_savings":        _fmt_usd(monthly_savings / n),
            "fleet_monthly_before":        cost["current_monthly_fmt"],
            "fleet_monthly_after":         cost["target_monthly_fmt"],
            "fleet_monthly_savings":       cost["monthly_savings_fmt"],
            "fleet_annual_savings":        cost["annual_savings_fmt"],
            "savings_pct":                 _fmt_pct(cost["savings_pct"]),
            "roi_months":                  cost["roi_months"],
        },

        "projections": {
            "3_months_usd":  _fmt_usd(monthly_savings * 3),
            "6_months_usd":  _fmt_usd(monthly_savings * 6),
            "12_months_usd": _fmt_usd(monthly_savings * 12),
            "24_months_usd": _fmt_usd(monthly_savings * 24),
            "36_months_usd": _fmt_usd(monthly_savings * 36),
        },

        "executive_summary": base["executive_summary"],
    }


# ─── Performance Impact ───────────────────────────────────────────────────────

def build_performance_impact(simulation: Any) -> Dict[str, Any]:
    """Focused performance and risk report."""
    base = build_simulation_summary(simulation)
    return {
        "report_type":      "performance_impact",
        "generated_at":     base["generated_at"],
        "simulation_name":  simulation.name,
        "simulation_id":    str(simulation.id),
        "risk_assessment":  base["risk_assessment"],
        "resource_analysis": base["resource_analysis"],
        "recommendation":   base["recommendation"],
        "recommendations":  base["recommendations"],
        "data_driven":      base["data_driven"],
        "executive_summary": base["executive_summary"],
    }


# ─── Dispatcher ──────────────────────────────────────────────────────────────

def generate_report_content(
    report_type: str,
    simulation: Optional[Any] = None,
    experiment: Optional[Any] = None,
) -> Dict[str, Any]:
    if report_type == "simulation_summary" and simulation:
        return build_simulation_summary(simulation)
    if report_type == "experiment_comparison" and experiment:
        return build_experiment_comparison(experiment)
    if report_type == "cost_analysis" and simulation:
        return build_cost_analysis(simulation)
    if report_type == "performance_impact" and simulation:
        return build_performance_impact(simulation)
    return {
        "report_type": report_type,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": "No source data linked to this report.",
    }
