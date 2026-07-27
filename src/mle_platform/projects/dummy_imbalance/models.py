from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def candidate_factories(seed: int = 42) -> dict[str, Callable[[], Any]]:
    """Return two intentionally compact, operationally distinct candidates.

    The linear model is an excellent independently packaged fallback: cheap,
    stable, interpretable, and based on a different failure surface from the
    tree ensemble. The random forest is the nonlinear challenger/champion.
    """

    return {
        "balanced_logistic": lambda: Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    LogisticRegression(
                        class_weight="balanced",
                        max_iter=2_000,
                        random_state=seed,
                    ),
                ),
            ]
        ),
        "balanced_random_forest": lambda: Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=160,
                        max_depth=8,
                        min_samples_leaf=4,
                        class_weight="balanced_subsample",
                        n_jobs=1,
                        random_state=seed,
                    ),
                ),
            ]
        ),
    }
