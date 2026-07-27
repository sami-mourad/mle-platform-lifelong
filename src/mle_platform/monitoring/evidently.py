"""Evidently report adapter with explicit no-data behavior."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import pandas as pd

from .delayed_labels import DelayedLabelPopulationBuilder

_NUMERIC_TYPES = (int, float)
_METRIC_IDENTITY_KEYS = {
    "metric",
    "metric_id",
    "metric_name",
    "name",
    "type",
    "config",
    "metric_config",
}
_COUNT_KEYS = (
    "count",
    "number_of_drifted_columns",
    "drifted_columns_count",
    "value",
    "current",
    "result",
)


def _is_number(value: Any) -> bool:
    """Return whether a JSON value is a real number rather than a boolean."""
    return isinstance(value, _NUMERIC_TYPES) and not isinstance(value, bool)


def _contains_text(value: Any, needle: str) -> bool:
    """Search nested JSON-like identity metadata for a case-insensitive token."""
    target = needle.casefold()
    if isinstance(value, str):
        return target in value.casefold()
    if isinstance(value, dict):
        return any(
            target in str(key).casefold() or _contains_text(item, needle)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_text(item, needle) for item in value)
    return False


def _node_identifies_metric(
    payload: dict[str, Any],
    metric_name: str,
) -> bool:
    """Return whether a report node describes the requested metric."""
    return any(
        key in _METRIC_IDENTITY_KEYS and _contains_text(value, metric_name)
        for key, value in payload.items()
    )


def _unwrap_count(value: Any) -> float | int | None:
    """Unwrap Evidently count results across simple and full JSON encodings."""
    if _is_number(value):
        return cast(float | int, value)
    if isinstance(value, dict):
        for key in _COUNT_KEYS:
            if key not in value:
                continue
            found = _unwrap_count(value[key])
            if found is not None:
                return found
    elif isinstance(value, list) and len(value) == 1:
        return _unwrap_count(value[0])
    return None


def _find_metric_value(payload: Any, metric_name: str) -> float | int | None:
    """Find a named Evidently count metric without binding to UI layout."""
    if isinstance(payload, dict):
        for key in ("number_of_drifted_columns", "drifted_columns_count"):
            if key in payload:
                value = _unwrap_count(payload[key])
                if value is not None:
                    return value

        if _node_identifies_metric(payload, metric_name):
            value = _unwrap_count(payload)
            if value is not None:
                return value

        for key, value in payload.items():
            if metric_name.casefold() in str(key).casefold():
                found = _unwrap_count(value)
                if found is not None:
                    return found
            found = _find_metric_value(value, metric_name)
            if found is not None:
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = _find_metric_value(value, metric_name)
            if found is not None:
                return found
    return None


class EvidentlyMonitoringAdapter:
    def run(
        self,
        *,
        reference_population: pd.DataFrame,
        current_population: pd.DataFrame,
        feature_columns: Sequence[str],
        output_directory: str | Path,
        model_id: str,
        reference_id: str,
    ) -> dict[str, Path]:
        if reference_population.empty:
            raise ValueError("reference monitoring population cannot be empty")
        if current_population.empty:
            raise ValueError("current monitoring population cannot be empty")
        reports = DelayedLabelPopulationBuilder.run_reports(
            reference_population=reference_population,
            current_population=current_population,
            feature_columns=feature_columns,
            output_directory=output_directory,
            model_id=model_id,
            reference_id=reference_id,
        )
        normalized: dict[str, Path] = {}
        for name, path in reports.items():
            normalized[str(name)] = Path(path)
        return normalized

    @staticmethod
    def drifted_feature_count(report_json: str | Path) -> int:
        """Return Evidently's drifted-column count and fail if it is absent."""
        path = Path(report_json)
        payload: Any = json.loads(path.read_text())
        value = _find_metric_value(payload, "DriftedColumnsCount")
        if value is None:
            top_level = sorted(payload) if isinstance(payload, dict) else [type(payload).__name__]
            raise ValueError(
                "Evidently drift report does not expose a supported "
                "DriftedColumnsCount encoding: "
                f"path={path}, top_level={top_level}"
            )
        return round(float(value))
