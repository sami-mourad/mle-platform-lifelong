"""Contract-first adapter to Repository 1 without source duplication."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .feature_contract import SynthAMLFeatureContract


class TemporalMLEProjectAdapter:
    """Validate and expose approved temporal feature snapshots to the platform."""

    def __init__(self, contract: SynthAMLFeatureContract) -> None:
        self.contract = contract

    def load_feature_snapshot(self, path: str | Path) -> pd.DataFrame:
        """Load a Repository-1 Parquet snapshot and validate the model boundary."""
        frame = pd.read_parquet(path)
        return self.validate_feature_snapshot(frame)

    def validate_feature_snapshot(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Validate an already loaded snapshot without imposing an I/O engine."""
        frame = frame.copy()
        required = {
            self.contract.entity_join_key,
            self.contract.event_timestamp_column,
            "feature_schema_version",
            *self.contract.feature_columns,
        }
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"feature snapshot is missing columns: {sorted(missing)}")
        grain = [
            self.contract.entity_join_key,
            self.contract.event_timestamp_column,
        ]
        if frame[grain].duplicated().any():
            raise ValueError("feature snapshot grain is not unique")
        frame[self.contract.event_timestamp_column] = pd.to_datetime(
            frame[self.contract.event_timestamp_column],
            utc=True,
        )
        observed_versions = set(frame["feature_schema_version"].dropna().astype(str))
        if observed_versions != {self.contract.feature_schema_version}:
            raise ValueError(
                "feature snapshot schema version mismatch; "
                f"expected {self.contract.feature_schema_version!r}, "
                f"observed {sorted(observed_versions)!r}"
            )
        model_features = frame.loc[:, list(self.contract.feature_columns)]
        if model_features.isna().any().any():
            columns = model_features.columns[model_features.isna().any()].tolist()
            raise ValueError(f"model-facing feature columns contain nulls: {columns}")
        unsupported = [
            column
            for column in self.contract.feature_columns
            if not pd.api.types.is_numeric_dtype(model_features[column])
            and not pd.api.types.is_bool_dtype(model_features[column])
        ]
        if unsupported:
            raise ValueError(f"model-facing features must be numeric or bool: {unsupported}")
        return frame

    def training_table(
        self,
        *,
        snapshot: pd.DataFrame,
        target_column: str,
        label_available_timestamp_column: str | None = None,
        maturity_cutoff: object | None = None,
    ) -> pd.DataFrame:
        if target_column not in snapshot:
            raise ValueError(f"target column is missing: {target_column}")
        table = snapshot.copy()
        if label_available_timestamp_column is not None:
            if label_available_timestamp_column not in table:
                raise ValueError(
                    "label availability timestamp column is missing: "
                    f"{label_available_timestamp_column}"
                )
            if maturity_cutoff is None:
                raise ValueError("maturity_cutoff is required with label availability")
            timestamps = pd.to_datetime(
                table[label_available_timestamp_column],
                utc=True,
            )
            cutoff = pd.Timestamp(maturity_cutoff)
            cutoff = (
                cutoff.tz_localize("UTC") if cutoff.tzinfo is None else cutoff.tz_convert("UTC")
            )
            table = table.loc[timestamps <= cutoff].copy()
        if table.empty:
            raise ValueError("no matured training rows remain")
        if table[target_column].isna().any() or table[target_column].nunique() < 2:
            raise ValueError("training target must be non-null and contain both classes")
        return table
