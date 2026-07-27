import numpy as np

from mle_platform.metrics import CostPolicy, classification_metrics, select_threshold


def test_threshold_selection_respects_cost_and_returns_metrics() -> None:
    y = np.array([0, 0, 0, 1, 1])
    scores = np.array([0.05, 0.10, 0.40, 0.60, 0.90])
    threshold, metrics = select_threshold(y, scores, CostPolicy(minimum_recall=1.0))
    assert 0.0 <= threshold <= 1.0
    assert metrics["recall"] == 1.0


def test_classification_metrics_include_imbalance_metrics() -> None:
    result = classification_metrics(
        np.array([0, 0, 1, 1]),
        np.array([0.1, 0.2, 0.8, 0.9]),
        0.5,
        CostPolicy(),
    )
    assert result["pr_auc"] == 1.0
    assert result["expected_cost"] == 0.0
