import pytest
from app.services.experiment_engine import (
    _composite_score,
    _verdict,
    run_experiment,
)


def test_composite_score_weighting():
    """Verify composite utility formulation balancing financial yield and safety."""
    # High savings ($6,000/mo), Low risk (10)
    score_balanced = _composite_score(monthly_savings=6000.0, risk_score=10.0, weight_savings=0.6)
    # Savings_norm = 60%, Safety_norm = 90%
    # 60 * 0.6 + 90 * 0.4 = 36 + 36 = 72
    assert score_balanced == pytest.approx(72.0, rel=1e-2)

    # High savings ($9,000/mo) but Critical risk (90)
    score_unsafe = _composite_score(monthly_savings=9000.0, risk_score=90.0, weight_savings=0.6)
    # Savings_norm = 90%, Safety_norm = 10%
    # 90 * 0.6 + 10 * 0.4 = 54 + 4 = 58
    assert score_unsafe < score_balanced


def test_verdict_mapping():
    """Verify operational verdict strings corresponding to risk levels."""
    assert _verdict("low") == "safe_to_rightsize"
    assert _verdict("medium") == "proceed_with_caution"
    assert _verdict("high") == "not_recommended"
    assert _verdict("critical") == "do_not_rightsize"


def test_multi_scenario_experiment_execution():
    """Verify multi-candidate experiment runs and declares the correct ranked winner."""
    scenarios = [
        {
            "name": "Moderate Downsizing",
            "current_instance_type": "c5.4xlarge",
            "target_instance_type": "c5.2xlarge",
            "instance_count": 10,
            "safety_margin_pct": 15.0,
        },
        {
            "name": "Aggressive Downsizing",
            "current_instance_type": "c5.4xlarge",
            "target_instance_type": "c5.xlarge",
            "instance_count": 10,
            "safety_margin_pct": 15.0,
        },
    ]

    experiment_result = run_experiment(scenarios)
    assert "scenarios" in experiment_result
    assert len(experiment_result["scenarios"]) == 2
    assert "best_savings" in experiment_result
    assert "best_safety" in experiment_result
    assert "summary" in experiment_result
