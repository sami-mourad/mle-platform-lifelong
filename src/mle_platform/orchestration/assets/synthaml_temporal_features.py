"""Dagster boundary for an already-approved Repository-1 feature snapshot."""

from __future__ import annotations

from pathlib import Path

from mle_platform.projects.synthaml import SynthAMLFeatureContract, TemporalMLEProjectAdapter

from ._compat import asset_compat


@asset_compat(group_name="synthaml", compute_kind="temporal_mle")
def synthaml_feature_snapshot(
    feature_snapshot_path: str,
    feature_contract_path: str,
) -> str:
    contract = SynthAMLFeatureContract.read_json(feature_contract_path)
    adapter = TemporalMLEProjectAdapter(contract)
    adapter.load_feature_snapshot(feature_snapshot_path)
    return str(Path(feature_snapshot_path).resolve())
