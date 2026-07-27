from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


@dataclass(frozen=True)
class CostPolicy:
    false_negative_cost: float = 25.0
    false_positive_cost: float = 1.0
    minimum_recall: float = 0.80


def expected_cost(y_true: np.ndarray, y_pred: np.ndarray, policy: CostPolicy) -> float:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    del tn, tp
    return float((fp * policy.false_positive_cost) + (fn * policy.false_negative_cost))


def select_threshold(
    y_true: np.ndarray,
    scores: np.ndarray,
    policy: CostPolicy,
    max_candidates: int = 500,
) -> tuple[float, dict[str, float]]:
    quantiles = np.linspace(0.0, 1.0, min(max_candidates, len(scores)))
    candidates = np.unique(np.quantile(scores, quantiles))
    best: tuple[float, float, float, float] | None = None
    for threshold in candidates:
        predictions = (scores >= threshold).astype(int)
        recall = recall_score(y_true, predictions, zero_division=0)
        cost = expected_cost(y_true, predictions, policy)
        precision = precision_score(y_true, predictions, zero_division=0)
        recall_penalty = max(0.0, policy.minimum_recall - recall) * 1_000_000.0
        objective = cost + recall_penalty
        candidate = (objective, -precision, -recall, float(threshold))
        if best is None or candidate < best:
            best = candidate
    if best is None:
        raise ValueError("No threshold candidates were generated")
    threshold = best[3]
    predictions = (scores >= threshold).astype(int)
    return threshold, {
        "threshold": threshold,
        "expected_cost": expected_cost(y_true, predictions, policy),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
    }


def classification_metrics(
    y_true: np.ndarray,
    scores: np.ndarray,
    threshold: float,
    policy: CostPolicy,
) -> dict[str, float]:
    predictions = (scores >= threshold).astype(int)
    return {
        "roc_auc": float(roc_auc_score(y_true, scores)),
        "pr_auc": float(average_precision_score(y_true, scores)),
        "brier": float(brier_score_loss(y_true, scores)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "expected_cost": expected_cost(y_true, predictions, policy),
        "threshold": float(threshold),
        "positive_rate": float(np.mean(predictions)),
    }
