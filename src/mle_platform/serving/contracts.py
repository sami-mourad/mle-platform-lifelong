"""Transport-neutral serving request and response contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ServingStatus(StrEnum):
    SCORED = "scored"
    MANUAL_REVIEW = "manual_review"


class ScoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: int | str
    evaluation_timestamp: datetime
    expected_feature_schema_version: str | None = None

    @field_validator("evaluation_timestamp")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("evaluation_timestamp must be timezone-aware")
        return value


class ScoreResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1)
    entity_id: int | str
    evaluation_timestamp: datetime
    prediction_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
    status: ServingStatus
    release_id: str | None = None
    model_version: int | None = Field(default=None, ge=1)
    feature_schema_version: str | None = None
    fraud_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    decision_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    predicted_positive: bool | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def validate_status(self) -> ScoreResponse:
        if self.prediction_timestamp < self.evaluation_timestamp:
            raise ValueError(
                "prediction_timestamp cannot precede evaluation_timestamp"
            )
        if self.status is ServingStatus.SCORED:
            probability = self.fraud_probability
            threshold = self.decision_threshold
            predicted_positive = self.predicted_positive
            if (
                self.release_id is None
                or self.model_version is None
                or self.feature_schema_version is None
                or probability is None
                or threshold is None
                or predicted_positive is None
            ):
                raise ValueError(
                    "scored responses require complete release and decision identity"
                )
            expected = probability >= threshold
            if predicted_positive is not expected:
                raise ValueError(
                    "predicted_positive must match release threshold"
                )
            if self.reason is not None:
                raise ValueError("scored responses cannot include a failure reason")
        elif not self.reason:
            raise ValueError("manual-review responses require a reason")
        return self
