"""
scenario_simulator.py
──────────────────────
Handles scenario-based simulation and sensitivity analysis.

Supports Scenarios:
1. Normal Weekday Traffic (Baseline multiplier = 1.0)
2. Live Sports Event (Traffic surge = 2.5, higher latency factor)
3. Viral Video Spike (Traffic surge = 4.0, extreme concurrency stress)

Allows users to adjust parameters:
- Traffic Growth multiplier (default 1.0)
- CPU Threshold (default 80.0)
- Memory Threshold (default 85.0)
- Latency Target (default 250.0)
- Availability Target (default 99.9)
- Custom Instance Pricing override

Provides a sensitivity analysis function analyzing recommendations when key metrics shift +/- 20%.
Identifies which parameter triggers change (CPU, Memory, Latency, Availability).
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import numpy as np
from app.schemas.simulator import SimulationConfig
from app.services.predictor import RightsizingPredictor
from app.services.baseline_engine import INSTANCE_SPECS

SCENARIOS = {
    "normal_weekday": {
        "name": "Normal Weekday Traffic",
        "description": "Standard streaming cluster load with regular diurnal patterns.",
        "traffic_multiplier": 1.0,
        "base_cpu_loc": 35.0,
        "base_latency_loc": 110.0,
        "base_availability_loc": 99.98
    },
    "live_sports": {
        "name": "Live Sports Event",
        "description": "Massive sudden burst of concurrent viewers with higher peak transaction loads.",
        "traffic_multiplier": 2.5,
        "base_cpu_loc": 65.0,
        "base_latency_loc": 180.0,
        "base_availability_loc": 99.91
    },
    "viral_video": {
        "name": "Viral Video Spike",
        "description": "Extreme request surge testing bandwidth throughput and connection limits.",
        "traffic_multiplier": 4.0,
        "base_cpu_loc": 82.0,
        "base_latency_loc": 230.0,
        "base_availability_loc": 99.85
    }
}

def simulate_scenario(
    scenario_key: str,
    config: SimulationConfig,
    user_adjustments: Dict[str, Any],
    cpu_series: Optional[List[float]] = None,
    memory_series: Optional[List[float]] = None,
    latency_series: Optional[List[float]] = None,
    availability_series: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Executes a scenario-based simulation and sensitivity analysis.

    Simulates the operational impact of migrating current cloud nodes to target instance
    candidates under specific stress scenarios (Normal Weekday, Live Sports Surge, Viral Video Spike).

    Args:
        scenario_key: The scenario profile identifier ("normal_weekday", "live_sports", "viral_video").
        config: Base simulation configuration including current instance specs and time window.
        user_adjustments: User-tuned operational parameters including traffic growth factor,
                          CPU/memory safety thresholds, latency SLAs, and availability targets.
        cpu_series: Optional historical CPU utilization vector [0.0 - 100.0].
        memory_series: Optional historical memory utilization vector [0.0 - 100.0].
        latency_series: Optional historical latency vector (ms).
        availability_series: Optional historical uptime percentage vector.

    Returns:
        Structured dictionary containing candidate metrics, recommended sizing, cost savings,
        and sensitivity analysis tracking how recommendations shift under +/- 20% load perturbations.
    """
    scenario = SCENARIOS.get(scenario_key, SCENARIOS["normal_weekday"])
    
    # ── Step 1: Calculate Total Workload Multiplier ────────────────────────────
    # Combines baseline scenario surge factor (e.g. 2.5x for live sports) with user-defined growth
    traffic_growth = user_adjustments.get("traffic_growth", 1.0)
    total_multiplier = scenario["traffic_multiplier"] * traffic_growth

    # ── Step 2: Ingest or Synthesize Workload Telemetry Arrays ────────────────
    cpu_arr = np.array(cpu_series) if cpu_series else np.array([])
    mem_arr = np.array(memory_series) if memory_series else np.array([])
    lat_arr = np.array(latency_series) if latency_series else np.array([])
    avail_arr = np.array(availability_series) if availability_series else np.array([])

    # If historical telemetry is not passed, generate reproducible Gaussian synthetic telemetry
    if len(cpu_arr) == 0:
        rng = np.random.default_rng(42)
        hours = config.time_window_hours
        cpu_arr = np.clip(rng.normal(loc=scenario["base_cpu_loc"], scale=10, size=hours), 5, 95)
        mem_arr = np.clip(rng.normal(loc=scenario["base_cpu_loc"] + 15, scale=8, size=hours), 10, 95)
        lat_arr = np.clip(rng.normal(loc=scenario["base_latency_loc"], scale=25, size=hours), 50, 500)
        avail_arr = np.clip(rng.normal(loc=scenario["base_availability_loc"], scale=0.03, size=hours), 99.0, 100.0)

    # ── Step 3: Scale Metrics by Scenario Traffic Multipliers ────────────────
    # CPU scales directly with request volume; Memory scaling is dampened (0.6 elasticity factor)
    cpu_scaled = np.clip(cpu_arr * total_multiplier, 0.0, 100.0)
    mem_scaled = np.clip(mem_arr * (1.0 + (total_multiplier - 1.0) * 0.6), 0.0, 100.0)
    lat_scaled = lat_arr * (1.0 + (total_multiplier - 1.0) * 0.8)
    
    # Availability penalty: heavy load surges introduce minor packet queuing degradation
    avail_penalty = max(0.0, (total_multiplier - 1.0) * 0.05)
    avail_scaled = np.clip(avail_arr - avail_penalty, 90.0, 100.0)

    avg_cpu = float(np.mean(cpu_scaled))
    avg_mem = float(np.mean(mem_scaled))
    avg_lat = float(np.mean(lat_scaled))
    avg_avail = float(np.mean(avail_scaled))

    # ── Step 4: Extract Operator Constraints & SLA Thresholds ────────────────
    cpu_limit = user_adjustments.get("cpu_threshold", 80.0)
    mem_limit = user_adjustments.get("memory_threshold", 85.0)
    lat_limit = user_adjustments.get("latency_target", 250.0)
    avail_limit = user_adjustments.get("availability_target", 99.9)

    pricing_override = user_adjustments.get("instance_pricing", {})

    candidates_metrics = []
    
    # ── Step 5: Evaluate All Hardware Instance Candidates in Catalog ─────────
    for name, spec in INSTANCE_SPECS.items():
        cost_per_hour = pricing_override.get(name, spec["cost_per_hour"])
        # Compute monthly cost based on a standard 720-hour cloud billing cycle (24 * 30)
        monthly_cost = cost_per_hour * config.instance_count * 24 * 30

        # Hardware scaling factors: ratio of candidate capacity to current cluster baseline
        cpu_scale = spec["vcpu"] / config.current_vcpu if config.current_vcpu > 0 else 1.0
        mem_scale = spec["memory_gb"] / config.current_memory_gb if config.current_memory_gb > 0 else 1.0

        # Projected resource utilization under candidate specifications
        cand_cpu = min(100.0, avg_cpu / cpu_scale) if cpu_scale > 0 else avg_cpu
        cand_mem = min(100.0, avg_mem / mem_scale) if mem_scale > 0 else avg_mem
        
        # Latency model: saturation above baseline causes queuing delay amplification
        cand_lat = avg_lat * (1.0 + max(0.0, (cand_cpu - avg_cpu) / 100.0))
        
        # Availability model: severe saturation (>80% CPU or >85% RAM) risks thread starvation
        if cand_cpu > 80.0 or cand_mem > 85.0:
            cand_avail = max(90.0, avg_avail - 1.0)
        else:
            cand_avail = avg_avail

        # Boolean constraint checks against operator SLAs
        passes_latency = cand_lat <= lat_limit
        passes_avail = cand_avail >= avail_limit
        passes_cpu = cand_cpu <= cpu_limit
        passes_mem = cand_mem <= mem_limit
        is_valid = passes_latency and passes_avail and passes_cpu and passes_mem

        candidates_metrics.append({
            "instance_type": name,
            "monthly_cost": round(monthly_cost, 2),
            "avg_cpu": round(cand_cpu, 2),
            "avg_memory": round(cand_mem, 2),
            "avg_latency": round(cand_lat, 2),
            "availability": round(cand_avail, 4),
            "is_valid": is_valid,
            "failed_constraints": [
                c for c, p in [
                    (f"latency > {lat_limit}ms", not passes_latency),
                    (f"availability < {avail_limit}%", not passes_avail),
                    (f"cpu > {cpu_limit}%", not passes_cpu),
                    (f"memory > {mem_limit}%", not passes_mem)
                ] if p
            ]
        })

    valid_candidates = [c for c in candidates_metrics if c["is_valid"]]
    
    if not valid_candidates:
        recommended_candidate = next((c for c in candidates_metrics if c["instance_type"] == config.current_instance_type), candidates_metrics[-1])
        verdict = "keep_current"
        reasoning = "All candidate configurations violated SLA safety targets. Retained current spec."
    else:
        min_cost = min(c["monthly_cost"] for c in valid_candidates)
        cheapest_options = [c for c in valid_candidates if c["monthly_cost"] == min_cost]
        recommended_candidate = min(cheapest_options, key=lambda x: x["avg_cpu"])
        verdict = "downsize"
        reasoning = f"Cheapest valid choice satisfying all thresholds is '{recommended_candidate['instance_type']}'."

    current_candidate = next((c for c in candidates_metrics if c["instance_type"] == config.current_instance_type), candidates_metrics[-1])
    savings = current_candidate["monthly_cost"] - recommended_candidate["monthly_cost"]

    # ── Step 6: Sensitivity Analysis & Parameter Bottleneck Tracking ──────────
    # Tests how robust the recommendation is by perturbing 4 critical operational levers:
    # 1. Traffic surge (+20% volume growth)
    # 2. Stringent CPU policy (lowered to 65% ceiling)
    # 3. Aggressive latency SLA (tightened to 180 ms)
    # 4. Strict uptime SLA (raised to 99.95% availability)
    sensitivity = []
    tests = [
        {"param": "Traffic Surge (+20%)", "adjustments": {**user_adjustments, "traffic_growth": traffic_growth * 1.2}},
        {"param": "Strict CPU Limit (65%)", "adjustments": {**user_adjustments, "cpu_threshold": 65.0}},
        {"param": "Strict Latency Target (180ms)", "adjustments": {**user_adjustments, "latency_target": 180.0}},
        {"param": "Strict Availability Target (99.95%)", "adjustments": {**user_adjustments, "availability_target": 99.95}}
    ]

    for test in tests:
        # Re-evaluate all candidate topologies against perturbed parameter space
        test_valid = []
        for cand in candidates_metrics:
            spec = INSTANCE_SPECS[cand["instance_type"]]
            # Re-scale parameters for the perturbation test
            test_traffic_mult = scenario["traffic_multiplier"] * test["adjustments"].get("traffic_growth", 1.0)
            t_cpu = min(100.0, float(np.mean(cpu_arr * test_traffic_mult)) / cpu_scale)
            t_mem = min(100.0, float(np.mean(mem_arr * (1.0 + (test_traffic_mult - 1.0) * 0.6))) / mem_scale)
            t_lat = float(np.mean(lat_arr * (1.0 + (test_traffic_mult - 1.0) * 0.8))) * (1.0 + max(0.0, (t_cpu - avg_cpu) / 100.0))
            t_avail = float(np.mean(avail_scaled))
            
            p_cpu = test["adjustments"].get("cpu_threshold", 80.0)
            p_mem = test["adjustments"].get("memory_threshold", 85.0)
            p_lat = test["adjustments"].get("latency_target", 250.0)
            p_avail = test["adjustments"].get("availability_target", 99.9)

            if t_cpu <= p_cpu and t_mem <= p_mem and t_lat <= p_lat and t_avail >= p_avail:
                test_valid.append(cand)
        
        test_rec = recommended_candidate["instance_type"]
        trigger_reason = "No Change"
        
        # If perturbation invalidates all downsizing options, fall back to current cluster baseline
        if not test_valid:
            test_rec = config.current_instance_type
        else:
            test_min_cost = min(c["monthly_cost"] for c in test_valid)
            test_cheapest = [c for c in test_valid if c["monthly_cost"] == test_min_cost]
            test_rec = min(test_cheapest, key=lambda x: x["avg_cpu"])["instance_type"]
            
        if test_rec != recommended_candidate["instance_type"]:
            trigger_reason = f"Parameter change triggered bottleneck. Recommends: {test_rec}"

        sensitivity.append({
            "assumption_shift": test["param"],
            "result_recommendation": test_rec,
            "trigger_reason": trigger_reason
        })

    return {
        "scenario_key": scenario_key,
        "scenario_name": scenario["name"],
        "scenario_description": scenario["description"],
        "current_configuration": current_candidate,
        "recommended_configuration": recommended_candidate,
        "candidates": candidates_metrics,
        "estimated_monthly_savings": round(savings, 2),
        "reasoning": reasoning,
        "sensitivity_analysis": sensitivity
    }
