import pandas as pd
import pytest
from sklearn.datasets import make_classification

from mle_platform.metrics import CostPolicy, classification_metrics, select_threshold
from mle_platform.projects.dummy_imbalance.data import (
    TARGET_COLUMN,
    split_dataset,
    validate_dataset,
)
from mle_platform.projects.dummy_imbalance.models import candidate_factories


@pytest.mark.integration
def test_each_candidate_trains_on_small_imbalanced_data() -> None:
    X, y = make_classification(
        n_samples=300,
        n_features=6,
        n_informative=5,
        n_redundant=1,
        weights=[0.95, 0.05],
        random_state=42,
    )
    frame = pd.DataFrame(X, columns=[f"attr{i}" for i in range(1, 7)])
    frame[TARGET_COLUMN] = y
    validate_dataset(frame)
    split = split_dataset(frame)
    for factory in candidate_factories().values():
        model = factory()
        model.fit(split.X_train, split.y_train)
        scores = model.predict_proba(split.X_validation)[:, 1]
        threshold, _ = select_threshold(split.y_validation, scores, CostPolicy())
        metrics = classification_metrics(split.y_validation, scores, threshold, CostPolicy())
        assert 0.0 <= metrics["pr_auc"] <= 1.0
