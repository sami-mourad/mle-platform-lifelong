from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import fetch_openml, make_classification
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DatasetSplit:
    X_train: pd.DataFrame
    X_validation: pd.DataFrame
    X_test: pd.DataFrame
    y_train: np.ndarray
    y_validation: np.ndarray
    y_test: np.ndarray


TARGET_COLUMN = "target"


def load_dataset(cache_path: Path, allow_synthetic_fallback: bool = True) -> pd.DataFrame:
    """Load a genuine imbalanced dataset and cache it as CSV.

    The OpenML Mammography dataset is small enough for local development and has
    a strongly imbalanced positive class. A deterministic synthetic fallback is
    available only to keep offline tests and disaster-recovery drills runnable.
    The data source is recorded in the returned frame attributes.
    """

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists():
        frame = pd.read_csv(cache_path)
        frame.attrs["source"] = "cache"
        return frame

    try:
        bunch = fetch_openml(name="mammography", version=1, as_frame=True, parser="auto")
        features = bunch.data.copy()
        target = pd.Series(bunch.target, name=TARGET_COLUMN)
        features.columns = [str(column) for column in features.columns]
        for column in features.columns:
            features[column] = pd.to_numeric(features[column], errors="coerce")
        values = sorted(str(value) for value in target.dropna().unique())
        positive = values[-1]
        encoded = (target.astype(str) == positive).astype(int)
        frame = features.assign(**{TARGET_COLUMN: encoded})
        frame.to_csv(cache_path, index=False)
        frame.attrs["source"] = "openml:mammography:v1"
        return frame
    except Exception:
        if not allow_synthetic_fallback:
            raise
        logger.exception(
            "OpenML download failed; using deterministic synthetic disaster-recovery data"
        )
        X, y = make_classification(
            n_samples=11_183,
            n_features=6,
            n_informative=5,
            n_redundant=1,
            weights=[0.977, 0.023],
            class_sep=1.2,
            random_state=42,
        )
        frame = pd.DataFrame(X, columns=[f"attr{i}" for i in range(1, 7)])
        frame[TARGET_COLUMN] = y
        frame.attrs["source"] = "synthetic_disaster_recovery_only"
        return frame


def validate_dataset(frame: pd.DataFrame) -> dict[str, float | int | str]:
    if TARGET_COLUMN not in frame:
        raise ValueError(f"Dataset must contain {TARGET_COLUMN!r}")
    if frame.empty:
        raise ValueError("Dataset is empty")
    target_values = set(frame[TARGET_COLUMN].dropna().astype(int).unique())
    if not target_values.issubset({0, 1}) or len(target_values) < 2:
        raise ValueError(f"Expected binary target with both classes, got {target_values}")
    positive_rate = float(frame[TARGET_COLUMN].mean())
    if not 0.001 <= positive_rate <= 0.40:
        raise ValueError(f"Unexpected positive rate {positive_rate:.4f}")
    numeric = frame.drop(columns=[TARGET_COLUMN])
    if numeric.shape[1] < 2:
        raise ValueError("Expected at least two features")
    return {
        "rows": len(frame),
        "features": int(numeric.shape[1]),
        "positive_rate": positive_rate,
        "missing_fraction": float(numeric.isna().mean().mean()),
        "source": str(frame.attrs.get("source", "unknown")),
    }


def split_dataset(
    frame: pd.DataFrame,
    *,
    seed: int = 42,
    validation_size: float = 0.20,
    test_size: float = 0.20,
) -> DatasetSplit:
    X = frame.drop(columns=[TARGET_COLUMN])
    y = frame[TARGET_COLUMN].astype(int).to_numpy()
    X_train_validation, X_test, y_train_validation, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        stratify=y,
        random_state=seed,
    )
    validation_share = validation_size / (1.0 - test_size)
    X_train, X_validation, y_train, y_validation = train_test_split(
        X_train_validation,
        y_train_validation,
        test_size=validation_share,
        stratify=y_train_validation,
        random_state=seed,
    )
    return DatasetSplit(
        X_train=X_train.reset_index(drop=True),
        X_validation=X_validation.reset_index(drop=True),
        X_test=X_test.reset_index(drop=True),
        y_train=y_train,
        y_validation=y_validation,
        y_test=y_test,
    )
