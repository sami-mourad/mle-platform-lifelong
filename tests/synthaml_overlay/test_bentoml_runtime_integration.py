from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from mle_platform.registry.mlflow import MLflowRegistryAdapter
from mle_platform.serving.bentoml_runtime import BentoMLReleaseRuntime

pytest.importorskip("mlflow")
pytest.importorskip("bentoml")
pytest.importorskip("sklearn")

pytestmark = pytest.mark.integration


def training_table() -> pd.DataFrame:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    rows: list[dict[str, object]] = []
    for index in range(50):
        feature_a = float(index % 6)
        feature_b = float((index % 4) - 1)
        rows.append(
            {
                "AlertID": index,
                "evaluation_timestamp": start + timedelta(hours=index),
                "a": feature_a,
                "b": feature_b,
                "target": int(feature_a >= 4 or feature_b > 1),
            }
        )
    return pd.DataFrame(rows)


def test_immutable_mlflow_version_imports_and_scores_through_bento(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BENTOML_HOME", str(tmp_path / "bento"))
    registry = MLflowRegistryAdapter(
        tracking_uri=f"sqlite:///{tmp_path / 'mlflow.db'}",
        artifact_root=tmp_path / "artifacts",
        experiment_name="bento-overlay-test",
        registered_model_name="bento-overlay-model",
    )
    result = registry.train_register_release(
        training_table=training_table(),
        feature_columns=("a", "b"),
        target_column="target",
        feature_schema_version="temporal_feature_schema_v3_1",
        feature_service_name="service",
        output_directory=str(tmp_path / "release"),
        decision_threshold=0.5,
        promote_to_champion=False,
    )
    runtime = BentoMLReleaseRuntime(model_name="bento-overlay-model")
    probability = runtime.predict_probability(
        manifest=result.release_manifest,
        feature_values={"a": 5.0, "b": 1.0},
    )
    assert 0.0 <= probability <= 1.0

    second = runtime.predict_probability(
        manifest=result.release_manifest,
        feature_values={"a": 1.0, "b": -1.0},
    )
    assert 0.0 <= second <= 1.0
