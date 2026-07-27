from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from mle_platform.contracts.synthaml import ModelReleaseManifest, TrainingDatasetManifest
from mle_platform.projects.synthaml.serving import SynthAMLServingApplication
from mle_platform.release.release_manifest import AtomicReleaseManifestRepository
from mle_platform.serving.contracts import ScoreRequest, ServingStatus
from mle_platform.serving.feature_retrieval import FeatureRetrievalService
from mle_platform.serving.prediction_log import JsonlPredictionLog


class FakeStore:
    def historical_features(self, request):
        raise NotImplementedError

    def materialize(self, **kwargs):
        return None

    def online_features(self, request):
        return {"view:a": [1.0], "view:b": [2.0]}


class FakeRuntime:
    def predict_probability(self, *, manifest, feature_values):
        assert feature_values == {"a": 1.0, "b": 2.0}
        return 0.8


def release() -> ModelReleaseManifest:
    return ModelReleaseManifest(
        release_id="r1",
        registered_model_name="model",
        model_version=1,
        mlflow_run_id="run",
        mlflow_model_uri="models:/model/1",
        feature_service_name="service",
        feature_schema_version="temporal_feature_schema_v3_1",
        decision_threshold=0.6,
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


def test_scored_response_and_prediction_trace(tmp_path: Path) -> None:
    manifests = AtomicReleaseManifestRepository(tmp_path / "releases")
    manifests.publish(release())
    log = JsonlPredictionLog(tmp_path / "predictions.jsonl")
    application = SynthAMLServingApplication(
        manifests=manifests,
        features=FeatureRetrievalService(
            store=FakeStore(),
            feature_service_name="service",
            feature_schema_version="temporal_feature_schema_v3_1",
            feature_columns=("a", "b"),
        ),
        runtime=FakeRuntime(),
        prediction_log=log,
    )
    response = application.score(
        ScoreRequest(
            entity_id=7,
            evaluation_timestamp=datetime(2025, 1, 1, tzinfo=UTC),
        )
    )
    assert response.status is ServingStatus.SCORED
    assert response.predicted_positive is True
    events = log.read_all()
    assert len(events) == 1
    assert events[0].release_id == "r1"


def test_missing_feature_routes_to_explicit_manual_review(tmp_path: Path) -> None:
    manifests = AtomicReleaseManifestRepository(tmp_path / "releases")
    manifests.publish(release())

    class MissingStore(FakeStore):
        def online_features(self, request):
            return {"view:a": [1.0]}

    application = SynthAMLServingApplication(
        manifests=manifests,
        features=FeatureRetrievalService(
            store=MissingStore(),
            feature_service_name="service",
            feature_schema_version="temporal_feature_schema_v3_1",
            feature_columns=("a", "b"),
        ),
        runtime=FakeRuntime(),
        prediction_log=JsonlPredictionLog(tmp_path / "predictions.jsonl"),
    )
    response = application.score(
        ScoreRequest(
            entity_id=7,
            evaluation_timestamp=datetime(2025, 1, 1, tzinfo=UTC),
        )
    )
    assert response.status is ServingStatus.MANUAL_REVIEW
    assert "missing" in response.reason
