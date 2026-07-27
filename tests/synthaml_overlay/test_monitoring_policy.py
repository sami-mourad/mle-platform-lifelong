from mle_platform.monitoring.monitoring_policy import MonitoringDecision, MonitoringPolicy


def test_empty_or_tiny_current_population_is_not_healthy() -> None:
    policy = MonitoringPolicy(minimum_current_rows=20)
    decision, reasons = policy.evaluate(
        current_row_count=0,
        drifted_feature_count=0,
        monitored_feature_count=5,
        summary={"matured_fraction": 0.0},
    )
    assert decision is MonitoringDecision.NO_DATA
    assert reasons


def test_drift_and_low_maturity_require_investigation() -> None:
    policy = MonitoringPolicy(
        minimum_current_rows=10,
        maximum_drifted_feature_fraction=0.2,
        minimum_matured_fraction=0.5,
    )
    decision, reasons = policy.evaluate(
        current_row_count=100,
        drifted_feature_count=2,
        monitored_feature_count=5,
        summary={"matured_fraction": 0.25},
    )
    assert decision is MonitoringDecision.INVESTIGATE
    assert len(reasons) == 2


def test_required_recall_is_fail_closed_when_unavailable() -> None:
    policy = MonitoringPolicy(
        minimum_current_rows=1,
        minimum_matured_fraction=0.0,
        minimum_recall=0.7,
    )
    decision, reasons = policy.evaluate(
        current_row_count=10,
        drifted_feature_count=0,
        monitored_feature_count=3,
        summary={"matured_fraction": 1.0, "recall": None},
    )
    assert decision is MonitoringDecision.INVESTIGATE
    assert "unavailable" in reasons[0]
