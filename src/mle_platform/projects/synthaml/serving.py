"""One strict entity-to-prediction journey for the SynthAML project."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from mle_platform.contracts.synthaml import (
    ModelReleaseManifest,
    PredictionTraceContract,
)
from mle_platform.release.release_manifest import AtomicReleaseManifestRepository
from mle_platform.serving.contracts import ScoreRequest, ScoreResponse, ServingStatus
from mle_platform.serving.decision_policy import ReleaseDecisionPolicy
from mle_platform.serving.feature_retrieval import (
    FeatureContractViolation,
    FeatureRetrievalService,
)
from mle_platform.serving.prediction_log import JsonlPredictionLog


class ReleaseRuntimePort(Protocol):
    """Runtime behavior required by the project serving application."""

    def predict_probability(
        self,
        *,
        manifest: ModelReleaseManifest,
        feature_values: Mapping[str, float | int | bool],
    ) -> float:
        """Return one calibrated fraud probability for an immutable release."""


class SynthAMLServingApplication:
    def __init__(
        self,
        *,
        manifests: AtomicReleaseManifestRepository,
        features: FeatureRetrievalService,
        runtime: ReleaseRuntimePort,
        prediction_log: JsonlPredictionLog,
        manual_review_on_error: bool = True,
    ) -> None:
        self.manifests = manifests
        self.features = features
        self.runtime = runtime
        self.prediction_log = prediction_log
        self.manual_review_on_error = manual_review_on_error

    def score(self, request: ScoreRequest) -> ScoreResponse:
        request_id = uuid4().hex
        try:
            manifest = self.manifests.load_active()
            if (
                request.expected_feature_schema_version is not None
                and request.expected_feature_schema_version
                != manifest.feature_schema_version
            ):
                raise FeatureContractViolation(
                    "requested feature schema is not active"
                )
            vector = self.features.retrieve(entity_id=request.entity_id)
            if vector.feature_schema_version != manifest.feature_schema_version:
                raise FeatureContractViolation(
                    "online feature schema does not match active model release"
                )
            probability = self.runtime.predict_probability(
                manifest=manifest,
                feature_values=vector.values,
            )
            decision = ReleaseDecisionPolicy.decide(
                probability=probability,
                manifest=manifest,
            )
            prediction_timestamp = datetime.now(UTC)
            trace = PredictionTraceContract(
                sample_id=request_id,
                entity_id=request.entity_id,
                evaluation_timestamp=request.evaluation_timestamp,
                prediction_timestamp=prediction_timestamp,
                release_id=manifest.release_id,
                model_version=manifest.model_version,
                feature_schema_version=manifest.feature_schema_version,
                fraud_probability=decision.probability,
                decision_threshold=decision.threshold,
                decision=decision.predicted_positive,
                feature_values=vector.values,
            )
            self.prediction_log.append(trace)
            return ScoreResponse(
                request_id=request_id,
                entity_id=request.entity_id,
                evaluation_timestamp=request.evaluation_timestamp,
                prediction_timestamp=prediction_timestamp,
                status=ServingStatus.SCORED,
                release_id=manifest.release_id,
                model_version=manifest.model_version,
                feature_schema_version=manifest.feature_schema_version,
                fraud_probability=decision.probability,
                decision_threshold=decision.threshold,
                predicted_positive=decision.predicted_positive,
            )
        except Exception as error:
            if not self.manual_review_on_error:
                raise
            return ScoreResponse(
                request_id=request_id,
                entity_id=request.entity_id,
                evaluation_timestamp=request.evaluation_timestamp,
                status=ServingStatus.MANUAL_REVIEW,
                reason=f"{type(error).__name__}: {error}",
            )
