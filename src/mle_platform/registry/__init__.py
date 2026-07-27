from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RegisteredVersion:
    name: str
    version: str
    model_uri: str


def configure_mlflow(tracking_uri: str | None, experiment_name: str) -> bool:
    if not tracking_uri:
        return False
    try:
        import mlflow

        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment_name)
        return True
    except Exception:
        logger.exception("Unable to configure MLflow; continuing with local artifacts")
        return False


def register_and_alias(
    *,
    run_id: str,
    artifact_path: str,
    registered_model_name: str,
    alias: str,
    tags: dict[str, str] | None = None,
) -> RegisteredVersion:
    import mlflow
    from mlflow import MlflowClient

    model_uri = f"runs:/{run_id}/{artifact_path}"
    model_version = mlflow.register_model(model_uri=model_uri, name=registered_model_name)
    client = MlflowClient()
    client.set_registered_model_alias(
        name=registered_model_name,
        alias=alias,
        version=model_version.version,
    )
    for key, value in (tags or {}).items():
        client.set_model_version_tag(
            name=registered_model_name,
            version=model_version.version,
            key=key,
            value=value,
        )
    return RegisteredVersion(
        name=registered_model_name,
        version=str(model_version.version),
        model_uri=f"models:/{registered_model_name}@{alias}",
    )


def log_json_artifact(payload: dict[str, Any], artifact_file: str) -> None:
    import mlflow

    mlflow.log_dict(payload, artifact_file)
