from __future__ import annotations

from pathlib import Path

from mle_platform.contracts.synthaml import ModelReleaseManifest, TrainingDatasetManifest
from mle_platform.release.release_manifest import AtomicReleaseManifestRepository


def manifest(release_id: str, version: int) -> ModelReleaseManifest:
    return ModelReleaseManifest(
        release_id=release_id,
        registered_model_name="model",
        model_version=version,
        mlflow_run_id=f"run-{version}",
        mlflow_model_uri=f"models:/model/{version}",
        feature_service_name="service",
        feature_schema_version="temporal_feature_schema_v3_1",
        decision_threshold=0.4,
        training_dataset_manifest=TrainingDatasetManifest(
            dataset_uri="file:///training.parquet",
            row_count=10,
            feature_count=2,
            feature_columns=("a", "b"),
            target_column="target",
            feature_schema_version="temporal_feature_schema_v3_1",
            split_policy="time_ordered",
        ),
    )


def test_atomic_active_pointer_and_history(tmp_path: Path) -> None:
    repository = AtomicReleaseManifestRepository(tmp_path)
    first = manifest("r1", 1)
    second = manifest("r2", 2)
    repository.publish(first)
    repository.publish(second)
    assert repository.load_active().release_id == "r2"
    assert repository.load_release("r1").model_version == 1
