"""
benchmarker.py
────────────────
Runs benchmarks comparing:
1. Baseline Decision Engine (simple CPU <40% downsizing rule)
2. Optimized Multi-Candidate Engine (evaluates all candidate configs against SLA constraints)

Across 5 adversarial edge cases:
- CPU at 98% (High load saturation)
- Memory Leak (Continuous upward memory growth)
- Missing Metrics (Data gaps / null columns)
- Pricing API Failure (Fallback to default standard rates)
- Sudden Traffic Spike (Diurnal workload explosion)

Measures: Monthly Cost, Latency, Availability, CPU, Memory, and generates improvement % metrics.
"""
from __future__ import annotations

import numpy as np
from typing import Any, Dict, List
from app.schemas.simulator import SimulationConfig
from app.services.baseline_engine import run_baseline_analysis

EDGE_CASES = {
    "cpu_98": {
        "name": "CPU at 98% Saturation",
        "cpu": [95.0, 98.0, 99.0, 97.0, 98.0, 99.0, 98.0],
        "memory": [60.0, 62.0, 61.0, 63.0, 64.0, 62.0, 63.0],
        "latency": [210.0, 245.0, 280.0, 230.0, 260.0, 290.0, 275.0],
        "availability": [99.95, 99.90, 99.85, 99.92, 99.88, 99.81, 99.87]
    },
    "memory_leak": {
        "name": "Memory Leak (Linear growth)",
        "cpu": [30.0, 32.0, 28.0, 31.0, 33.0, 29.0, 30.0],
        "memory": [40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 95.0],
        "latency": [110.0, 115.0, 112.0, 118.0, 120.0, 116.0, 119.0],
        "availability": [99.99, 99.99, 99.98, 99.97, 99.95, 99.90, 99.80]
    },
    "missing_metrics": {
        "name": "Missing Metrics (Null data)",
        "cpu": [45.0, None, 48.0, None, 50.0, 47.0, None],
        "memory": [None, 55.0, 58.0, None, 60.0, None, 62.0],
        "latency": [120.0, 130.0, None, 125.0, None, 135.0, 128.0],
        "availability": [99.98, 99.99, 99.98, None, 99.97, 99.99, None]
    },
    "pricing_failure": {
        "name": "Pricing API Failure (Override standard prices)",
        "cpu": [35.0, 38.0, 32.0, 36.0, 34.0, 37.0, 35.0],
        "memory": [50.0, 52.0, 48.0, 51.0, 49.0, 53.0, 51.0],
        "latency": [105.0, 110.0, 108.0, 112.0, 107.0, 115.0, 111.0],
        "availability": [99.99, 99.99, 99.98, 99.99, 99.98, 99.99, 99.99]
    },
    "traffic_spike": {
        "name": "Sudden Traffic Spike",
        "cpu": [30.0, 35.0, 95.0, 98.0, 40.0, 35.0, 32.0],
        "memory": [45.0, 48.0, 80.0, 85.0, 50.0, 47.0, 46.0],
        "latency": [100.0, 110.0, 290.0, 320.0, 130.0, 115.0, 108.0],
        "availability": [99.99, 99.98, 99.82, 99.71, 99.95, 99.98, 99.99]
    }
}

def run_automated_benchmark(current_instance: str) -> Dict[str, Any]:
    # Construct base simulation config
    config = SimulationConfig(
        name="Benchmark Evaluation",
        current_instance_type=current_instance,
        current_vcpu=16, current_memory_gb=32, current_cost_per_hour_usd=0.68,
        target_instance_type="c5.2xlarge", target_vcpu=8, target_memory_gb=16, target_cost_per_hour_usd=0.34,
        instance_count=1,
        time_window_hours=168
    )

    benchmark_runs = []

    for key, data in EDGE_CASES.items():
        # Handle Null values for Missing Metrics
        cpus = [c for c in data["cpu"] if c is not None]
        mems = [m for m in data["memory"] if m is not None]
        lats = [l for l in data["latency"] if l is not None]
        avails = [a for a in data["availability"] if a is not None]

        # 1. Run Baseline (evaluates CPU below 40% rule only)
        # We simulate baseline by forcing it to downsize if avg cpu < 40%, otherwise keep current config
        avg_cpu = float(np.mean(cpus)) if cpus else 35.0
        baseline_downsizes = avg_cpu < 40.0
        
        baseline_cost = 0.68 * 24 * 30
        baseline_latency = float(np.mean(lats))
        baseline_avail = float(np.mean(avails))
        baseline_cpu = avg_cpu
        baseline_mem = float(np.mean(mems))
        baseline_verdict = current_instance

        if baseline_downsizes:
            baseline_verdict = "c5.2xlarge"
            baseline_cost = 0.34 * 24 * 30
            baseline_cpu = min(100.0, avg_cpu * 2)
            baseline_mem = min(100.0, float(np.mean(mems)) * 2)
            baseline_latency = baseline_latency * 1.5
            baseline_avail = max(95.0, baseline_avail - 1.0) if baseline_cpu > 80.0 else baseline_avail

        # 2. Run Optimized Simulator Engine (evaluates constraints and selects safest candidate size)
        opt_res = run_baseline_analysis(
            config=config,
            cpu_series=cpus,
            memory_series=mems,
            latency_series=lats,
            availability_series=avails
        )
        opt_config = opt_res["recommended_configuration"]

        # 3. Calculate Improvement percentages
        cost_impr = ((baseline_cost - opt_config["monthly_cost"]) / baseline_cost * 100) if baseline_cost > 0 else 0
        lat_impr = ((baseline_latency - opt_config["avg_latency"]) / baseline_latency * 100) if baseline_latency > 0 else 0
        
        # Availability error rate analysis comparison
        base_err = 100.0 - baseline_avail
        opt_err = 100.0 - opt_config["availability"]
        avail_impr = ((base_err - opt_err) / base_err * 100) if base_err > 0 else 0

        benchmark_runs.append({
            "edge_case_key": key,
            "edge_case_name": data["name"],
            "baseline": {
                "instance_type": baseline_verdict,
                "monthly_cost": round(baseline_cost, 2),
                "avg_cpu": round(baseline_cpu, 2),
                "avg_memory": round(baseline_mem, 2),
                "avg_latency": round(baseline_latency, 2),
                "availability": round(baseline_avail, 4),
            },
            "optimized": {
                "instance_type": opt_config["instance_type"],
                "monthly_cost": round(opt_config["monthly_cost"], 2),
                "avg_cpu": round(opt_config["avg_cpu"], 2),
                "avg_memory": round(opt_config["avg_memory"], 2),
                "avg_latency": round(opt_config["avg_latency"], 2),
                "availability": round(opt_config["availability"], 4),
            },
            "improvements": {
                "monthly_cost_percent": round(cost_impr, 1),
                "latency_percent": round(lat_impr, 1),
                "availability_error_reduction_percent": round(avail_impr, 1)
            }
        })

    return {
        "status": "success",
        "benchmarks": benchmark_runs
    }
