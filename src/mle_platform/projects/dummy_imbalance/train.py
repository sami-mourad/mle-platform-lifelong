from __future__ import annotations

import json
import logging
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from mle_platform.config import get_settings
from mle_platform.contracts import DeploymentPaths
from mle_platform.io import atomic_write_json, sha256_file
from mle_platform.logging import configure_logging
from mle_platform.metrics import CostPolicy, classification_metrics, select_threshold
from mle_platform.projects.dummy_imbalance.data import load_dataset, split_dataset, validate_dataset
from mle_platform.projects.dummy_imbalance.models import candidate_factories
from mle_platform.registry import configure_mlflow, register_and_alias

logger = logging.getLogger(__name__)


@dataclass
class CandidateResult:
    name: str
    model: Any
    validation_metrics: dict[str, float]
    test_metrics: dict[str, float]
    threshold: float
    run_id: str | None = None
    model_version: str = "local"


def _fit_candidate(
    name: str,
    model: Any,
    split: Any,
    policy: CostPolicy,
    mlflow_enabled: bool,
) -> CandidateResult:
    run = None
    if mlflow_enabled:
        import mlflow

        run = mlflow.start_run(run_name=name)
        mlflow.log_params({"candidate": name, "model_class": type(model).__name__})
    try:
        model.fit(split.X_train, split.y_train)
        validation_scores = np.asarray(model.predict_proba(split.X_validation))[:, 1]
        threshold, threshold_metrics = select_threshold(
            split.y_validation, validation_scores, policy
        )
        validation_metrics = classification_metrics(
            split.y_validation, validation_scores, threshold, policy
        )
        test_scores = np.asarray(model.predict_proba(split.X_test))[:, 1]
        test_metrics = classification_metrics(split.y_test, test_scores, threshold, policy)
        if mlflow_enabled:
            import mlflow
            import mlflow.sklearn

            mlflow.log_metrics({f"validation_{k}": v for k, v in validation_metrics.items()})
            mlflow.log_metrics({f"test_{k}": v for k, v in test_metrics.items()})
            mlflow.log_dict(threshold_metrics, "evaluation/threshold_selection.json")
            input_example = split.X_validation.head(5)
            mlflow.sklearn.log_model(
                sk_model=model,
                name="model",
                input_example=input_example,
            )
        return CandidateResult(
            name=name,
            model=model,
            validation_metrics=validation_metrics,
            test_metrics=test_metrics,
            threshold=threshold,
            run_id=run.info.run_id if run is not None else None,
        )
    finally:
        if mlflow_enabled:
            import mlflow

            mlflow.end_run()


def _ranking_key(result: CandidateResult) -> tuple[float, float, float]:
    # Primary objective reflects decision cost. PR-AUC and Brier score are tie-breakers.
    return (
        result.validation_metrics["expected_cost"],
        -result.validation_metrics["pr_auc"],
        result.validation_metrics["brier"],
    )


def train_and_promote() -> dict[str, Any]:
    settings = get_settings()
    configure_logging(settings.log_level)
    cache_path = settings.data_dir / "mammography.csv"
    frame = load_dataset(cache_path)
    profile = validate_dataset(frame)
    split = split_dataset(frame)
    policy = CostPolicy()

    mlflow_enabled = configure_mlflow(
        settings.mlflow_tracking_uri,
        settings.mlflow_experiment_name,
    )

    candidates = [
        _fit_candidate(name, factory(), split, policy, mlflow_enabled)
        for name, factory in candidate_factories().items()
    ]
    candidates.sort(key=_ranking_key)
    champion, fallback = candidates[0], candidates[1]

    if mlflow_enabled and settings.mlflow_register_models:
        if champion.run_id is None or fallback.run_id is None:
            raise RuntimeError("MLflow run IDs are required for model registration")
        champion_registration = register_and_alias(
            run_id=champion.run_id,
            artifact_path="model",
            registered_model_name=settings.mlflow_model_name,
            alias="champion",
            tags={"candidate": champion.name, "role": "champion"},
        )
        fallback_registration = register_and_alias(
            run_id=fallback.run_id,
            artifact_path="model",
            registered_model_name=settings.mlflow_model_name,
            alias="fallback",
            tags={"candidate": fallback.name, "role": "fallback"},
        )
        champion.model_version = champion_registration.version
        fallback.model_version = fallback_registration.version

    deployment_paths = DeploymentPaths(settings.artifact_dir)
    settings.artifact_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=settings.artifact_dir) as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        champion_temp = temp_dir / "champion.joblib"
        fallback_temp = temp_dir / "fallback.joblib"
        joblib.dump(champion.model, champion_temp)
        joblib.dump(fallback.model, fallback_temp)
        shutil.move(str(champion_temp), deployment_paths.champion_model)
        shutil.move(str(fallback_temp), deployment_paths.fallback_model)

    release_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    report = {
        "release_id": release_id,
        "dataset_profile": profile,
        "candidates": {
            result.name: {
                "validation": result.validation_metrics,
                "test": result.test_metrics,
                "threshold": result.threshold,
                "run_id": result.run_id,
                "model_version": result.model_version,
            }
            for result in candidates
        },
        "selection_rule": "minimum validation expected cost, then maximum PR-AUC, then minimum Brier",
    }
    atomic_write_json(deployment_paths.evaluation_report, report)

    manifest = {
        "schema_version": 1,
        "release_id": release_id,
        "created_at": datetime.now(UTC).isoformat(),
        "feature_names": list(split.X_train.columns),
        "dataset_source": profile["source"],
        "champion": {
            "name": champion.name,
            "version": champion.model_version,
            "threshold": champion.threshold,
            "sha256": sha256_file(deployment_paths.champion_model),
            "run_id": champion.run_id,
        },
        "fallback": {
            "name": fallback.name,
            "version": fallback.model_version,
            "threshold": fallback.threshold,
            "sha256": sha256_file(deployment_paths.fallback_model),
            "run_id": fallback.run_id,
        },
        "rules_fallback": {
            "name": "conservative_manual_review",
            "version": "1",
            "behavior": "route to manual review when both learned models are unavailable",
        },
    }
    # Manifest is the atomic release pointer and must be written last.
    atomic_write_json(deployment_paths.manifest, manifest)
    logger.info(
        "Promotion completed",
        extra={"model_source": "champion", "model_version": release_id},
    )
    return {"manifest": manifest, "report": report}


def main() -> None:
    result = train_and_promote()
    print(json.dumps(result["manifest"], indent=2))


if __name__ == "__main__":
    main()
