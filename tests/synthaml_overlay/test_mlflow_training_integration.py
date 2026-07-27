from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from mle_platform.projects.synthaml import (
    SynthAMLFeatureContract,
    SynthAMLTrainingService,
)
from mle_platform.registry.mlflow import MLflowRegistryAdapter
from mle_platform.release.promotion_policy import (
    MetricRequirement,
    PromotionPolicy,
)
from mle_platform.release.release_manifest import AtomicReleaseManifestRepository
from mle_platform.release.rollback import ReleaseController

pytest.importorskip("mlflow")
pytest.importorskip("sklearn")

pytestmark = pytest.mark.integration


def table() -> pd.DataFrame:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    rows: list[dict[str, object]] = []
    for index in range(60):
        feature_a = float(index % 7)
        feature_b = float((index % 5) - 2)
        rows.append(
            {
                "AlertID": index,
                "evaluation_timestamp": start + timedelta(hours=index),
                "a": feature_a,
                "b": feature_b,
                "target": int(feature_a > 4 or feature_b > 1),
            }
        )
    return pd.DataFrame(rows)


def test_training_promotion_and_active_release(tmp_path: Path) -> None:
    contract = SynthAMLFeatureContract(
        contract_version="v1",
        temporal_package_version="3.1.1",
        feature_schema_version="temporal_feature_schema_v3_1",
        feature_service_name="service",
        feature_view_name="view",
        entity_name="entity",
        entity_join_key="AlertID",
        event_timestamp_column="evaluation_timestamp",
        feature_columns=("a", "b"),
        feature_dtypes={"a": "FLOAT64", "b": "FLOAT64"},
    )
    registry = MLflowRegistryAdapter(
        tracking_uri=f"sqlite:///{tmp_path / 'mlflow.db'}",
        artifact_root=tmp_path / "artifacts",
        experiment_name="overlay-test",
        registered_model_name="overlay-test-model",
    )
    manifests = AtomicReleaseManifestRepository(tmp_path / "releases")
    service = SynthAMLTrainingService(
        contract=contract,
        registry=registry,
        promotion_policy=PromotionPolicy(
            [
                MetricRequirement("validation_f1", minimum=0.0),
                MetricRequirement("validation_brier_score", maximum=1.0),
            ]
        ),
        release_controller=ReleaseController(
            registry=registry,
            manifests=manifests,
        ),
    )
    result, decision = service.train_candidate(
        training_table=table(),
        target_column="target",
        output_directory=tmp_path / "training",
        decision_threshold=0.5,
    )
    assert decision.approved
    assert (
        manifests.load_active().release_id
        == result.release_manifest.release_id
    )
    assert (
        registry.model_version(
            model_name="overlay-test-model",
            alias="champion",
        )
        >= 1
    )
