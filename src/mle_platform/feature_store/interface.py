"""Tool-independent historical and online feature retrieval contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class HistoricalFeatureRequest:
    """Point-in-time feature request for a bounded entity table."""

    entity_dataframe: Any
    feature_service_name: str
    full_feature_names: bool = True


@dataclass(frozen=True)
class OnlineFeatureRequest:
    """Latest materialized feature request for serving entities."""

    entity_rows: tuple[Mapping[str, Any], ...]
    feature_service_name: str
    full_feature_names: bool = True


@runtime_checkable
class FeatureStorePort(Protocol):
    """Minimal feature-store behavior required by training and serving."""

    def historical_features(self, request: HistoricalFeatureRequest) -> Any:
        """Return a point-in-time-correct historical feature table."""

    def materialize(
        self,
        *,
        start: datetime,
        end: datetime,
        feature_views: Sequence[str] | None = None,
    ) -> None:
        """Publish approved offline rows to an online store."""

    def online_features(
        self,
        request: OnlineFeatureRequest,
    ) -> Mapping[str, list[Any]]:
        """Return latest materialized features for entity rows."""
