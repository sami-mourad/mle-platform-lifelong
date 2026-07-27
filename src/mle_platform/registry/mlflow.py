"""MLflow implementation of the platform registry seam."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


class MLflowRegistryAdapter:
    """Own tracking configuration while reusing Repository 1's proven trainer."""

    def __init__(
        self,
        *,
        tracking_uri: str,
        artifact_root: str | Path,
        experiment_name: str,
        registered_model_name: str,
    ) -> None:
        try:
            from temporal_mle.platform_integration import MLflowLocalRegistryTrainer
        except ImportError as error:
            raise RuntimeError(
                "Repository 1 (temporal-mle) is required for the MLflow training slice."
            ) from error
        self.model_name = registered_model_name
        self._trainer = MLflowLocalRegistryTrainer(
            tracking_uri=tracking_uri,
            artifact_root=artifact_root,
            experiment_name=experiment_name,
            registered_model_name=registered_model_name,
        )

    @property
    def client(self) -> Any:
        return self._trainer.client

    def train_register_release(
        self,
        *,
        training_table: Any,
        feature_columns: Sequence[str],
        target_column: str,
        feature_schema_version: str,
        feature_service_name: str,
        output_directory: str,
        decision_threshold: float = 0.5,
        promote_to_champion: bool = False,
        code_revision: str | None = None,
        run_tags: Mapping[str, str] | None = None,
    ) -> Any:
        return self._trainer.train_register_release(
            training_table=training_table,
            feature_columns=feature_columns,
            target_column=target_column,
            feature_schema_version=feature_schema_version,
            feature_service_name=feature_service_name,
            output_directory=output_directory,
            decision_threshold=decision_threshold,
            promote_to_champion=promote_to_champion,
            code_revision=code_revision,
            run_tags=run_tags,
        )

    def set_alias(self, *, model_name: str, alias: str, model_version: int) -> None:
        self.client.set_registered_model_alias(model_name, alias, str(model_version))

    def load_model(self, *, model_name: str, alias_or_version: str | int) -> Any:
        import mlflow.pyfunc

        if isinstance(alias_or_version, int) or str(alias_or_version).isdigit():
            uri = f"models:/{model_name}/{alias_or_version}"
        else:
            uri = f"models:/{model_name}@{alias_or_version}"
        return mlflow.pyfunc.load_model(uri)

    def model_version(self, *, model_name: str, alias: str) -> int:
        return int(self.client.get_model_version_by_alias(model_name, alias).version)
