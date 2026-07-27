"""Dagster check-like boundary for a promotion decision."""

from __future__ import annotations

from typing import Any

from ._compat import asset_compat


@asset_compat(group_name="synthaml", compute_kind="release")
def synthaml_active_release(candidate_result: tuple[Any, Any]) -> str:
    result, decision = candidate_result
    if not decision.approved:
        raise RuntimeError(f"candidate did not pass promotion policy: {decision.reasons}")
    return result.release_manifest.release_id
