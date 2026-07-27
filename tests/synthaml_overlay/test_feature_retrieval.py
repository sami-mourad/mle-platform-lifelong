from __future__ import annotations

import pytest

from mle_platform.serving.feature_retrieval import FeatureContractViolation, FeatureRetrievalService


class FakeStore:
    def __init__(self, payload):
        self.payload = payload

    def historical_features(self, request):
        raise NotImplementedError

    def materialize(self, **kwargs):
        return None

    def online_features(self, request):
        return self.payload


def test_strict_retrieval_rejects_missing_or_null() -> None:
    service = FeatureRetrievalService(
        store=FakeStore({"view:a": [1.0]}),
        feature_service_name="service",
        feature_schema_version="temporal_feature_schema_v3_1",
        feature_columns=("a", "b"),
    )
    with pytest.raises(FeatureContractViolation, match="missing"):
        service.retrieve(entity_id=1)

    service = FeatureRetrievalService(
        store=FakeStore({"view:a": [1.0], "view:b": [None]}),
        feature_service_name="service",
        feature_schema_version="temporal_feature_schema_v3_1",
        feature_columns=("a", "b"),
    )
    with pytest.raises(FeatureContractViolation, match="null"):
        service.retrieve(entity_id=1)


def test_strict_retrieval_preserves_ordered_values() -> None:
    service = FeatureRetrievalService(
        store=FakeStore({"view:a": [1.0], "view:b": [2.0]}),
        feature_service_name="service",
        feature_schema_version="temporal_feature_schema_v3_1",
        feature_columns=("a", "b"),
    )
    vector = service.retrieve(entity_id=1)
    assert vector.values == {"a": 1.0, "b": 2.0}


def test_strict_retrieval_rejects_ambiguous_full_names() -> None:
    service = FeatureRetrievalService(
        store=FakeStore({"view_a:a": [1.0], "view_b:a": [2.0]}),
        feature_service_name="service",
        feature_schema_version="temporal_feature_schema_v3_1",
        feature_columns=("a",),
    )
    with pytest.raises(FeatureContractViolation, match="ambiguous"):
        service.retrieve(entity_id=1)
