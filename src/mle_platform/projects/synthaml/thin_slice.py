"""Dependency-light proof that Repository 2 can host a SynthAML release.

This module contains reusable platform-composition logic. The executable under
``examples/`` is intentionally only a command-line wrapper, so tests and
installed consumers never depend on the examples directory being importable.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from mle_platform.contracts.synthaml import (
    ModelReleaseManifest,
    TrainingDatasetManifest,
)
from mle_platform.release.release_manifest import AtomicReleaseManifestRepository
from mle_platform.serving.contracts import ScoreRequest
from mle_platform.serving.feature_retrieval import FeatureRetrievalService
from mle_platform.serving.prediction_log import JsonlPredictionLog

from .adapter import TemporalMLEProjectAdapter
from .feature_contract import SynthAMLFeatureContract
from .serving import SynthAMLServingApplication

DEFAULT_CONTRACT_PATH = Path("contracts/synthaml/feature_contract_v3_1_1.json")


class InMemoryFeatureStore:
    """Small feature-store port used only by the dependency-light proof."""

    def __init__(self, feature_values: Mapping[str, float | int | bool]) -> None:
        self.feature_values = dict(feature_values)

    def historical_features(self, request: Any) -> Any:
        del request
        raise NotImplementedError("historical retrieval belongs to the Feast gate")

    def materialize(self, **kwargs: Any) -> None:
        del kwargs
        raise NotImplementedError("materialization belongs to the Feast gate")

    def online_features(self, request: Any) -> dict[str, list[float | int | bool]]:
        del request
        return {
            f"synthaml_temporal_features:{name}": [value]
            for name, value in self.feature_values.items()
        }


class DeterministicRuntime:
    """Small runtime port used only to prove platform composition."""

    def predict_probability(
        self,
        *,
        manifest: ModelReleaseManifest,
        feature_values: Mapping[str, float | int | bool],
    ) -> float:
        ordered = manifest.training_dataset_manifest.feature_columns
        values = [float(feature_values[name]) for name in ordered]
        raw = 0.15 + 0.08 * values[0] + 0.002 * values[1] - 0.0005 * values[2]
        return min(1.0, max(0.0, raw))


def feature_snapshot(contract: SynthAMLFeatureContract) -> pd.DataFrame:
    """Create one validated fixture row for the composition proof."""
    return pd.DataFrame(
        {
            contract.entity_join_key: [930],
            contract.event_timestamp_column: [
                datetime(2025, 1, 31, 12, tzinfo=UTC)
            ],
            "feature_schema_version": [contract.feature_schema_version],
            "transaction_count": [7.0],
            "absolute_transaction_amount_flow": [125.0],
            "interarrival_time_mean_seconds": [90.0],
            "target": [1],
        }
    )


def build_release(contract: SynthAMLFeatureContract) -> ModelReleaseManifest:
    """Build an immutable release identity for the deterministic runtime."""
    dataset = TrainingDatasetManifest(
        dataset_uri="memory://validated-synthaml-thin-slice",
        row_count=1,
        feature_count=len(contract.feature_columns),
        feature_columns=contract.feature_columns,
        target_column="target",
        feature_schema_version=contract.feature_schema_version,
        split_policy="not-applicable-platform-composition-smoke",
    )
    return ModelReleaseManifest(
        release_id="synthaml-thin-slice-v1",
        created_timestamp=datetime(2025, 1, 31, 12, 5, tzinfo=UTC),
        registered_model_name="synthaml_fraud_detector",
        model_version=1,
        mlflow_run_id="thin-slice-no-mlflow",
        mlflow_model_uri="memory://deterministic-runtime",
        feature_service_name=contract.feature_service_name,
        feature_schema_version=contract.feature_schema_version,
        decision_threshold=0.5,
        training_dataset_manifest=dataset,
        metrics={"composition_smoke": 1.0},
        tags={"evidence_level": "platform-core"},
    )


def run(
    output_directory: Path,
    *,
    contract_path: str | Path = DEFAULT_CONTRACT_PATH,
) -> dict[str, Any]:
    """Execute the dependency-light release, score, trace, and failure journey."""
    contract = SynthAMLFeatureContract.read_json(contract_path)
    snapshot = TemporalMLEProjectAdapter(contract).validate_feature_snapshot(
        feature_snapshot(contract)
    )

    output_directory.mkdir(parents=True, exist_ok=True)
    predictions_path = output_directory / "predictions.jsonl"
    evidence_path = output_directory / "hosting_thin_slice_evidence.json"
    predictions_path.unlink(missing_ok=True)
    evidence_path.unlink(missing_ok=True)

    manifests = AtomicReleaseManifestRepository(output_directory / "releases")
    active_release = build_release(contract)
    manifests.publish(active_release)

    values = {name: snapshot.loc[0, name] for name in contract.feature_columns}
    prediction_log = JsonlPredictionLog(predictions_path)
    application = SynthAMLServingApplication(
        manifests=manifests,
        features=FeatureRetrievalService(
            store=InMemoryFeatureStore(values),
            feature_service_name=contract.feature_service_name,
            feature_schema_version=contract.feature_schema_version,
            feature_columns=contract.feature_columns,
            entity_join_key=contract.entity_join_key,
        ),
        runtime=DeterministicRuntime(),
        prediction_log=prediction_log,
    )
    scored = application.score(
        ScoreRequest(
            entity_id=930,
            evaluation_timestamp=snapshot.loc[
                0, contract.event_timestamp_column
            ],
            expected_feature_schema_version=contract.feature_schema_version,
        )
    )

    incomplete_values = {
        name: value
        for name, value in values.items()
        if name != contract.feature_columns[-1]
    }
    broken = SynthAMLServingApplication(
        manifests=manifests,
        features=FeatureRetrievalService(
            store=InMemoryFeatureStore(incomplete_values),
            feature_service_name=contract.feature_service_name,
            feature_schema_version=contract.feature_schema_version,
            feature_columns=contract.feature_columns,
            entity_join_key=contract.entity_join_key,
        ),
        runtime=DeterministicRuntime(),
        prediction_log=prediction_log,
    ).score(
        ScoreRequest(
            entity_id=930,
            evaluation_timestamp=snapshot.loc[
                0, contract.event_timestamp_column
            ],
        )
    )

    evidence = {
        "evidence_level": "platform-core-thin-slice",
        "feature_contract_version": contract.contract_version,
        "feature_schema_version": contract.feature_schema_version,
        "validated_snapshot_rows": len(snapshot),
        "validated_feature_columns": list(contract.feature_columns),
        "active_release_id": manifests.load_active().release_id,
        "scored_response": scored.model_dump(mode="json"),
        "manual_review_response": broken.model_dump(mode="json"),
        "prediction_trace_count": len(prediction_log.read_all()),
        "external_sdk_claims": {
            "feast": False,
            "mlflow": False,
            "bentoml": False,
            "evidently": False,
        },
    }
    evidence_path.write_text(json.dumps(evidence, indent=2))
    return {**evidence, "evidence_path": str(evidence_path)}
