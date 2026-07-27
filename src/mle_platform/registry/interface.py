"""Model registry behavior required by release management."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ModelRegistryPort(Protocol):
    def train_register_release(
        self,
        *,
        training_table: Any,
        feature_columns: Sequence[str],
        target_column: str,
        feature_schema_version: str,
        feature_service_name: str,
        output_directory: str,
        decision_threshold: float,
        promote_to_champion: bool,
        code_revision: str | None = None,
        run_tags: Mapping[str, str] | None = None,
    ) -> Any:
        """Train and register one candidate release."""

    def set_alias(self, *, model_name: str, alias: str, model_version: int) -> None:
        """Move one mutable registry alias to an immutable model version."""

    def load_model(self, *, model_name: str, alias_or_version: str | int) -> Any:
        """Load a model through an explicit alias or version."""
