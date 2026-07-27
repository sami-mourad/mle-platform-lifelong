"""Dagster boundary for Feast materialization and parity evidence."""

from __future__ import annotations

from datetime import datetime

from mle_platform.feature_store.feast import FeastFeatureStoreAdapter

from ._compat import asset_compat


@asset_compat(group_name="synthaml", compute_kind="feast")
def synthaml_feast_materialization(
    feature_repo_path: str,
    start_timestamp: datetime,
    end_timestamp: datetime,
) -> dict[str, str]:
    store = FeastFeatureStoreAdapter(feature_repo_path)
    store.materialize(start=start_timestamp, end=end_timestamp)
    return {
        "feature_repo_path": feature_repo_path,
        "start_timestamp": start_timestamp.isoformat(),
        "end_timestamp": end_timestamp.isoformat(),
    }
