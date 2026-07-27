from __future__ import annotations

from pathlib import Path

import pytest

from mle_platform.contracts.synthaml import ModelReleaseManifest, TrainingDatasetManifest
from mle_platform.release.release_manifest import AtomicReleaseManifestRepository
from mle_platform.release.rollback import ReleaseController


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


class Registry:
    def __init__(self) -> None:
        self.alias_versions: list[int] = []

    def set_alias(self, *, model_name: str, alias: str, model_version: int) -> None:
        assert model_name == "model"
        assert alias == "champion"
        self.alias_versions.append(model_version)

    def train_register_release(self, **kwargs):
        raise NotImplementedError

    def load_model(self, **kwargs):
        raise NotImplementedError


class FailingPublishRepository(AtomicReleaseManifestRepository):
    def publish(self, release):
        if release.release_id == "r2":
            raise OSError("simulated pointer failure")
        return super().publish(release)


def test_activation_compensates_alias_when_pointer_publish_fails(tmp_path: Path) -> None:
    registry = Registry()
    manifests = FailingPublishRepository(tmp_path)
    controller = ReleaseController(registry=registry, manifests=manifests)
    controller.activate(manifest("r1", 1))

    with pytest.raises(OSError, match="pointer failure"):
        controller.activate(manifest("r2", 2))

    assert registry.alias_versions == [1, 2, 1]
    assert manifests.load_active().release_id == "r1"
