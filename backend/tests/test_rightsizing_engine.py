import pytest
import numpy as np
from app.schemas.simulator import SimulationConfig
from app.services.rightsizing_engine import (
    analyse_resources,
    detect_trend,
    compute_risk,
    _risk_score,
    _risk_level,
    _pct_above,
    _percentile_safe,
    run_rightsizing_analysis,
)


def test_percentile_safe_empty_and_valid():
    """Verify that percentile calculation is robust against empty arrays."""
    assert _percentile_safe(np.array([]), 99) == 0.0
    arr = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    assert _percentile_safe(arr, 50) == 30.0


def test_pct_above_threshold():
    """Verify percentage calculation above threshold."""
    arr = np.array([20.0, 40.0, 60.0, 80.0, 100.0])
    # 2 out of 5 values (80 and 100) are > 70.0 -> 40%
    assert _pct_above(arr, 70.0) == 40.0
    assert _pct_above(np.array([]), 50.0) == 0.0


def test_risk_score_and_classification_boundaries():
    """Verify risk score formula bounds and 4-tier risk classification."""
    # Low Risk (< 15)
    score_low = _risk_score(breach_prob=5.0, safety_margin=15.0)
    assert score_low < 15.0
    assert _risk_level(score_low) == "low"

    # Medium Risk (15 - 34.9)
    score_med = _risk_score(breach_prob=20.0, safety_margin=10.0)
    assert 15.0 <= score_med < 35.0
    assert _risk_level(score_med) == "medium"

    # High Risk (35 - 64.9)
    score_high = _risk_score(breach_prob=40.0, safety_margin=5.0)
    assert 35.0 <= score_high < 65.0
    assert _risk_level(score_high) == "high"

    # Critical Risk (>= 65)
    score_crit = _risk_score(breach_prob=80.0, safety_margin=0.0)
    assert score_crit >= 65.0
    assert _risk_level(score_crit) == "critical"

    # Upper clamp limit
    assert _risk_score(breach_prob=150.0, safety_margin=0.0) == 100.0


def test_linear_regression_trend_detection():
    """Verify Scikit-learn trend slope and direction classification."""
    # Stable workload
    stable_series = np.array([50.0, 50.1, 49.9, 50.0, 50.2, 49.8])
    trend_stable = detect_trend(stable_series)
    assert trend_stable["direction"] == "stable"
    assert "r2" in trend_stable

    # Strictly increasing workload
    increasing_series = np.array([20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0])
    trend_inc = detect_trend(increasing_series)
    assert trend_inc["direction"] == "increasing"
    assert trend_inc["slope_pct_per_hour"] > 0
    assert trend_inc["r2"] > 0.95


def test_resource_scaling_and_projection():
    """Verify CPU and memory scaling projections from c5.4xlarge to c5.2xlarge."""
    config = SimulationConfig(
        name="Test Scaling",
        current_instance_type="c5.4xlarge",
        target_instance_type="c5.2xlarge",
        current_vcpu=16,
        current_memory_gb=32,
        target_vcpu=8,
        target_memory_gb=16,
        current_cost_per_hour_usd=0.68,
        target_cost_per_hour_usd=0.34,
        max_cpu_threshold_pct=80.0,
        max_memory_threshold_pct=85.0,
        safety_margin_pct=15.0,
        instance_count=10,
        time_window_hours=24,
    )

    cpu_hist = np.array([30.0, 35.0, 40.0, 32.0])
    mem_hist = np.array([40.0, 45.0, 50.0, 42.0])

    analysis = analyse_resources(cpu_hist, mem_hist, config)
    assert analysis["scaling_factors"]["cpu_scale"] == 0.5
    assert analysis["scaling_factors"]["memory_scale"] == 0.5

    # Projected mean should be approximately double historical mean
    assert analysis["projected_cpu"]["mean"] == pytest.approx(analysis["current_cpu"]["mean"] / 0.5, rel=1e-2)


def test_full_rightsizing_simulation_run():
    """Verify end-to-end execution of rightsizing analysis."""
    config = SimulationConfig(
        name="Test Rightsizing",
        current_instance_type="c5.4xlarge",
        target_instance_type="c5.2xlarge",
        current_vcpu=16,
        current_memory_gb=32,
        target_vcpu=8,
        target_memory_gb=16,
        current_cost_per_hour_usd=0.68,
        target_cost_per_hour_usd=0.34,
        max_cpu_threshold_pct=80.0,
        max_memory_threshold_pct=85.0,
        safety_margin_pct=15.0,
        instance_count=10,
        time_window_hours=24,
    )

    result = run_rightsizing_analysis(config)
    assert "performance_risk" in result
    assert "risk_score" in result["performance_risk"]
    assert "risk_level" in result["performance_risk"]
    assert "cost_savings" in result
    assert result["cost_savings"]["monthly_savings_usd"] == 2448.00
    assert result["cost_savings"]["current_monthly_cost_usd"] == 4896.00
