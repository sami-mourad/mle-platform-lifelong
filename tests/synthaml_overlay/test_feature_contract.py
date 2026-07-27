from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from mle_platform.projects.synthaml import SynthAMLFeatureContract, TemporalMLEProjectAdapter


def contract() -> SynthAMLFeatureContract:
    return SynthAMLFeatureContract(
        contract_version="v1",
        temporal_package_version="3.1.1",
        feature_schema_version="temporal_feature_schema_v3_1",
        feature_service_name="service",
        feature_view_name="view",
        entity_name="entity",
        entity_join_key="AlertID",
        event_timestamp_column="evaluation_timestamp",
        feature_columns=("a", "b"),
        feature_dtypes={"a": "FLOAT64", "b": "FLOAT64"},
    )


def valid_table() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "AlertID": [1, 2],
            "evaluation_timestamp": pd.to_datetime(["2025-01-01", "2025-01-02"], utc=True),
            "feature_schema_version": ["temporal_feature_schema_v3_1"] * 2,
            "a": [1.0, 2.0],
            "b": [3.0, 4.0],
        }
    )


def test_contract_round_trip(tmp_path: Path) -> None:
    path = contract().write_json(tmp_path / "contract.json")
    assert SynthAMLFeatureContract.read_json(path) == contract()


def test_snapshot_grain_and_nulls_fail_closed_in_memory() -> None:
    adapter = TemporalMLEProjectAdapter(contract())
    table = valid_table()
    table.loc[1, "AlertID"] = 1
    table.loc[1, "evaluation_timestamp"] = table.loc[0, "evaluation_timestamp"]
    with pytest.raises(ValueError, match="grain"):
        adapter.validate_feature_snapshot(table)

    table = valid_table()
    table.loc[1, "b"] = None
    with pytest.raises(ValueError, match="nulls"):
        adapter.validate_feature_snapshot(table)


def test_parquet_snapshot_uses_same_validation_boundary(tmp_path: Path) -> None:
    pytest.importorskip("pyarrow")
    adapter = TemporalMLEProjectAdapter(contract())
    table = valid_table()
    path = tmp_path / "snapshot.parquet"
    table.to_parquet(path)
    observed = adapter.load_feature_snapshot(path)
    assert observed[["AlertID", "a", "b"]].equals(table[["AlertID", "a", "b"]])


def test_training_table_respects_label_maturity() -> None:
    adapter = TemporalMLEProjectAdapter(contract())
    table = valid_table().assign(
        final_outcome=["Reported", "Dismissed"],
        label_available_timestamp=pd.to_datetime(["2025-01-03", "2025-01-04"], utc=True),
    )
    mature = adapter.training_table(
        snapshot=table,
        target_column="final_outcome",
        label_available_timestamp_column="label_available_timestamp",
        maturity_cutoff="2025-01-04T00:00:00Z",
    )
    assert len(mature) == 2

    with pytest.raises(ValueError, match="both classes"):
        adapter.training_table(
            snapshot=table,
            target_column="final_outcome",
            label_available_timestamp_column="label_available_timestamp",
            maturity_cutoff="2025-01-03T00:00:00Z",
        )


def test_training_table_names_missing_availability_column() -> None:
    adapter = TemporalMLEProjectAdapter(contract())
    table = valid_table().assign(final_outcome=["Reported", "Dismissed"])
    with pytest.raises(ValueError, match="availability timestamp column is missing"):
        adapter.training_table(
            snapshot=table,
            target_column="final_outcome",
            label_available_timestamp_column="label_available_timestamp",
            maturity_cutoff="2025-01-04T00:00:00Z",
        )
