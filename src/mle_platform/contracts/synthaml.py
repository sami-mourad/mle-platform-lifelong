"""Runtime representations of the versioned SynthAML boundary contracts.

The JSON Schemas under ``contracts/synthaml`` remain the cross-repository wire
contract. Repository 2 owns these runtime models because release, serving, and
monitoring are platform responsibilities. Repository 1 is required only at the
feature-production and Feast adapter boundary, not merely to import the
platform package.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class _ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SynthAMLFeatureSnapshotContract(_ContractModel):
    sample_id: str = Field(min_length=1)
    entity_id: int | str
    evaluation_timestamp: datetime
    feature_service_name: str = Field(min_length=1)
    feature_schema_version: str = Field(min_length=1)
    features: dict[str, float | int | bool | None] = Field(min_length=1)
    event_anchor_timestamp: datetime | None = None
    created_timestamp: datetime | None = None


class TrainingDatasetManifest(_ContractModel):
    dataset_uri: str
    row_count: int = Field(ge=1)
    feature_count: int = Field(ge=1)
    feature_columns: tuple[str, ...]
    target_column: str
    entity_column: str = "AlertID"
    evaluation_timestamp_column: str = "evaluation_timestamp"
    feature_schema_version: str
    split_policy: str
    label_maturity_cutoff: datetime | None = None
    content_sha256: str | None = None

    @model_validator(mode="after")
    def validate_feature_identity(self) -> TrainingDatasetManifest:
        if not self.feature_columns:
            raise ValueError("feature_columns cannot be empty")
        if len(set(self.feature_columns)) != len(self.feature_columns):
            raise ValueError("feature_columns must be unique")
        if self.feature_count != len(self.feature_columns):
            raise ValueError("feature_count must equal len(feature_columns)")
        return self


class ModelReleaseManifest(_ContractModel):
    release_id: str
    created_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    registered_model_name: str
    model_version: int = Field(ge=1)
    mlflow_run_id: str
    mlflow_model_uri: str
    candidate_alias: str = "candidate"
    champion_alias: str | None = None
    feature_service_name: str
    feature_schema_version: str
    decision_threshold: float = Field(ge=0.0, le=1.0)
    training_dataset_manifest: TrainingDatasetManifest
    code_revision: str | None = None
    metrics: dict[str, float] = Field(default_factory=dict)
    tags: dict[str, str] = Field(default_factory=dict)

    @field_validator("release_id")
    @classmethod
    def safe_release_id(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9._-]+", value):
            raise ValueError("release_id must be filename-safe")
        return value

    @model_validator(mode="after")
    def validate_release_identity(self) -> ModelReleaseManifest:
        if self.feature_schema_version != self.training_dataset_manifest.feature_schema_version:
            raise ValueError("release feature_schema_version must match the training dataset")
        return self


class PredictionTraceContract(_ContractModel):
    sample_id: str
    entity_id: int | str
    evaluation_timestamp: datetime
    prediction_timestamp: datetime
    release_id: str
    model_version: int = Field(ge=1)
    feature_schema_version: str
    fraud_probability: float = Field(ge=0.0, le=1.0)
    decision_threshold: float = Field(ge=0.0, le=1.0)
    decision: bool
    feature_values: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_trace(self) -> PredictionTraceContract:
        if self.prediction_timestamp < self.evaluation_timestamp:
            raise ValueError("prediction_timestamp cannot precede evaluation_timestamp")
        if self.decision is not (self.fraud_probability >= self.decision_threshold):
            raise ValueError("decision must match probability and release threshold")
        return self


__all__ = [
    "ModelReleaseManifest",
    "PredictionTraceContract",
    "SynthAMLFeatureSnapshotContract",
    "TrainingDatasetManifest",
]
