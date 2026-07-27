"""Dagster boundary for one known-entity serving smoke."""

from __future__ import annotations

from typing import Any

from ._compat import asset_compat


@asset_compat(group_name="synthaml", compute_kind="bentoml")
def synthaml_serving_smoke(application: Any, request: Any) -> dict[str, object]:
    response = application.score(request)
    if response.status.value != "scored":
        raise RuntimeError(f"serving smoke degraded: {response.reason}")
    return response.model_dump(mode="json")
