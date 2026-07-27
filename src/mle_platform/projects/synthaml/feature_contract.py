"""Project-owned declaration of the exact model-facing feature surface."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast


@dataclass(frozen=True)
class SynthAMLFeatureContract:
    contract_version: str
    temporal_package_version: str
    feature_schema_version: str
    feature_service_name: str
    feature_view_name: str
    entity_name: str
    entity_join_key: str
    event_timestamp_column: str
    feature_columns: tuple[str, ...]
    feature_dtypes: dict[str, str]

    def __post_init__(self) -> None:
        required_names = {
            "contract_version": self.contract_version,
            "temporal_package_version": self.temporal_package_version,
            "feature_schema_version": self.feature_schema_version,
            "feature_service_name": self.feature_service_name,
            "feature_view_name": self.feature_view_name,
            "entity_name": self.entity_name,
            "entity_join_key": self.entity_join_key,
            "event_timestamp_column": self.event_timestamp_column,
        }
        blank = [name for name, value in required_names.items() if not value.strip()]
        if blank:
            raise ValueError(f"contract fields cannot be blank: {sorted(blank)}")
        if not self.feature_columns:
            raise ValueError("feature_columns cannot be empty")
        if len(set(self.feature_columns)) != len(self.feature_columns):
            raise ValueError("feature_columns must be unique")
        if set(self.feature_columns) != set(self.feature_dtypes):
            raise ValueError("feature_dtypes must exactly cover feature_columns")

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, object],
    ) -> SynthAMLFeatureContract:
        feature_columns_value = payload.get("feature_columns")
        if not isinstance(feature_columns_value, Sequence) or isinstance(
            feature_columns_value, str | bytes
        ):
            raise ValueError("feature_columns must be a sequence")

        feature_dtypes_value = payload.get("feature_dtypes")
        if not isinstance(feature_dtypes_value, Mapping):
            raise ValueError("feature_dtypes must be a mapping")

        return cls(
            contract_version=str(payload["contract_version"]),
            temporal_package_version=str(payload["temporal_package_version"]),
            feature_schema_version=str(payload["feature_schema_version"]),
            feature_service_name=str(payload["feature_service_name"]),
            feature_view_name=str(payload["feature_view_name"]),
            entity_name=str(payload.get("entity_name", "aml_alert")),
            entity_join_key=str(payload.get("entity_join_key", "AlertID")),
            event_timestamp_column=str(
                payload.get("event_timestamp_column", "evaluation_timestamp")
            ),
            feature_columns=tuple(str(value) for value in feature_columns_value),
            feature_dtypes={str(key): str(value) for key, value in feature_dtypes_value.items()},
        )

    @classmethod
    def read_json(cls, path: str | Path) -> SynthAMLFeatureContract:
        payload: Any = json.loads(Path(path).read_text())
        if not isinstance(payload, Mapping):
            raise ValueError("feature contract JSON must contain an object")
        return cls.from_mapping(cast(Mapping[str, object], payload))

    def write_json(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(asdict(self), indent=2))
        return destination

    def feast_objects(self, *, parquet_path: str) -> dict[str, object]:
        try:
            from temporal_mle import FeastFeatureDefinitions
        except ImportError as error:
            raise RuntimeError(
                "Repository 1 (temporal-mle) is required to build Feast objects; "
                "install it with `python -m pip install -e "
                "../temporal-mle-data-contract`."
            ) from error
        result: Any = FeastFeatureDefinitions.build(
            parquet_path=parquet_path,
            feature_schema=self.feature_dtypes,
            entity_name=self.entity_name,
            join_key=self.entity_join_key,
            feature_view_name=self.feature_view_name,
            feature_service_name=self.feature_service_name,
            event_timestamp_column=self.event_timestamp_column,
        )
        if not isinstance(result, dict):
            raise TypeError("Repository 1 returned an invalid Feast object mapping")
        return cast(dict[str, object], result)
