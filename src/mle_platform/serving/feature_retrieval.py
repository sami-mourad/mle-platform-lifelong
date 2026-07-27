"""Strict serving feature retrieval; missing values are never silently zero-filled."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from mle_platform.feature_store.interface import FeatureStorePort, OnlineFeatureRequest


class FeatureContractViolation(ValueError):
    pass


@dataclass(frozen=True)
class RetrievedFeatureVector:
    entity_id: int | str
    feature_schema_version: str
    values: dict[str, float | int | bool]


class FeatureRetrievalService:
    def __init__(
        self,
        *,
        store: FeatureStorePort,
        feature_service_name: str,
        feature_schema_version: str,
        feature_columns: Sequence[str],
        entity_join_key: str = "AlertID",
    ) -> None:
        self.store = store
        self.feature_service_name = feature_service_name
        self.feature_schema_version = feature_schema_version
        self.feature_columns = tuple(feature_columns)
        self.entity_join_key = entity_join_key
        if not self.feature_columns or len(set(self.feature_columns)) != len(self.feature_columns):
            raise ValueError("feature_columns must be non-empty and unique")

    @staticmethod
    def _resolve_name(payload: Mapping[str, Sequence[Any]], feature: str) -> str | None:
        if feature in payload:
            return feature
        matches = [
            name
            for name in payload
            if name.endswith(f":{feature}") or name.endswith(f"__{feature}")
        ]
        if len(matches) > 1:
            raise FeatureContractViolation(
                f"online feature name is ambiguous for {feature}: {sorted(matches)}"
            )
        return matches[0] if matches else None

    def retrieve(self, *, entity_id: int | str) -> RetrievedFeatureVector:
        payload = self.store.online_features(
            OnlineFeatureRequest(
                entity_rows=({self.entity_join_key: entity_id},),
                feature_service_name=self.feature_service_name,
                full_feature_names=True,
            )
        )
        values: dict[str, float | int | bool] = {}
        for feature in self.feature_columns:
            actual_name = self._resolve_name(payload, feature)
            if actual_name is None:
                raise FeatureContractViolation(f"online feature is missing: {feature}")
            series = list(payload[actual_name])
            if len(series) != 1:
                raise FeatureContractViolation(
                    f"feature {feature} returned {len(series)} rows for one entity"
                )
            value = series[0]
            if value is None:
                raise FeatureContractViolation(f"online feature is null: {feature}")
            if not isinstance(value, (int, float, bool)):
                raise FeatureContractViolation(
                    f"feature {feature} has unsupported serving type {type(value).__name__}"
                )
            values[feature] = value
        return RetrievedFeatureVector(
            entity_id=entity_id,
            feature_schema_version=self.feature_schema_version,
            values=values,
        )
