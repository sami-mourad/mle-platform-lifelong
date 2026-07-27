"""Dagster boundary for the project training service."""

from __future__ import annotations

from typing import Any

from ._compat import asset_compat


@asset_compat(group_name="synthaml", compute_kind="mlflow")
def synthaml_model_candidate(training_service: Any, training_table: Any, **kwargs: Any) -> Any:
    return training_service.train_candidate(training_table=training_table, **kwargs)
