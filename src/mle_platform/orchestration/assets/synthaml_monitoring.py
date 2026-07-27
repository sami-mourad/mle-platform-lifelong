"""Dagster boundary for delayed-label monitoring."""

from __future__ import annotations

from typing import Any

from ._compat import asset_compat


@asset_compat(group_name="synthaml", compute_kind="evidently")
def synthaml_monitoring_observation(monitoring_service: Any, **kwargs: Any) -> str:
    return str(monitoring_service.run(**kwargs))
