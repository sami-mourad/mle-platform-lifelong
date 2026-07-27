"""Feast implementation of the platform feature-store port."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, cast

from .interface import HistoricalFeatureRequest, OnlineFeatureRequest


class FeastFeatureStoreAdapter:
    """Wrap Repository 1's Feast lifecycle behind a platform port."""

    def __init__(self, repository_path: str) -> None:
        try:
            from temporal_mle import FeastPointInTimeMaterializer
        except ImportError as error:
            raise RuntimeError(
                "Repository 1 (temporal-mle) is required for the Feast slice."
            ) from error
        self._lifecycle = FeastPointInTimeMaterializer(repository_path)

    @property
    def lifecycle(self) -> Any:
        return self._lifecycle

    def apply(self, objects: Sequence[object]) -> None:
        self._lifecycle.apply(objects)

    def historical_features(self, request: HistoricalFeatureRequest) -> Any:
        return self._lifecycle.build_training_set(
            entity_dataframe=request.entity_dataframe,
            feature_service_name=request.feature_service_name,
            full_feature_names=request.full_feature_names,
        )

    def materialize(
        self,
        *,
        start: datetime,
        end: datetime,
        feature_views: Sequence[str] | None = None,
    ) -> None:
        self._lifecycle.materialize(
            start=start,
            end=end,
            feature_views=feature_views,
        )

    def online_features(
        self,
        request: OnlineFeatureRequest,
    ) -> Mapping[str, list[Any]]:
        result: Any = self._lifecycle.online_features(
            feature_service_name=request.feature_service_name,
            entity_rows=request.entity_rows,
            full_feature_names=request.full_feature_names,
        )
        if not isinstance(result, Mapping):
            raise TypeError("Repository 1 returned invalid online feature data")
        return cast(Mapping[str, list[Any]], result)

    def parity_report(self, **kwargs: Any) -> Any:
        return self._lifecycle.parity_report(**kwargs)
