from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ScoreRequest(BaseModel):
    features: dict[str, float] = Field(min_length=1)

    @field_validator("features")
    @classmethod
    def reject_non_finite(cls, value: dict[str, float]) -> dict[str, float]:
        for name, item in value.items():
            if item != item or item in (float("inf"), float("-inf")):
                raise ValueError(f"Feature {name!r} must be finite")
        return value


class ScoreResponse(BaseModel):
    request_id: str
    score: float
    decision: str
    model_source: str
    model_name: str
    model_version: str
    threshold: float
    degraded: bool
    reason: str | None = None


class ReadinessResponse(BaseModel):
    status: str
    learned_model_loaded: bool
    release_id: str
