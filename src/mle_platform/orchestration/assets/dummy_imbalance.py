from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from dagster import AssetCheckResult, AssetExecutionContext, MetadataValue, asset, asset_check

from mle_platform.config import get_settings
from mle_platform.contracts import DeploymentPaths
from mle_platform.io import read_json
from mle_platform.projects.dummy_imbalance.data import load_dataset, validate_dataset
from mle_platform.projects.dummy_imbalance.train import train_and_promote


@asset(group_name="data", compute_kind="openml")
def raw_mammography_dataset(context: AssetExecutionContext) -> str:
    settings = get_settings()
    path = settings.data_dir / "mammography.csv"
    frame = load_dataset(path)
    context.add_output_metadata(
        {
            "rows": len(frame),
            "columns": len(frame.columns),
            "path": MetadataValue.path(str(path)),
            "source": frame.attrs.get("source", "unknown"),
        }
    )
    return str(path)


@asset(group_name="data", compute_kind="python")
def dataset_profile(
    context: AssetExecutionContext,
    raw_mammography_dataset: str,
) -> dict[str, object]:
    frame = load_dataset(Path(raw_mammography_dataset))
    profile = validate_dataset(frame)
    context.add_output_metadata(profile)
    return cast(dict[str, object], profile)


@asset(group_name="ml", compute_kind="scikit-learn")
def promoted_model_release(
    context: AssetExecutionContext,
    dataset_profile: dict[str, object],
) -> dict[str, object]:
    del dataset_profile
    result = train_and_promote()
    manifest = cast(dict[str, Any], result["manifest"])
    context.add_output_metadata(
        {
            "release_id": manifest["release_id"],
            "champion": manifest["champion"]["name"],
            "fallback": manifest["fallback"]["name"],
        }
    )
    return cast(dict[str, object], manifest)


@asset(group_name="deployment", compute_kind="manifest")
def deployment_manifest(
    context: AssetExecutionContext,
    promoted_model_release: dict[str, object],
) -> str:
    del promoted_model_release
    path = DeploymentPaths(get_settings().artifact_dir).manifest
    manifest = read_json(path)
    context.add_output_metadata(
        {
            "release_id": manifest["release_id"],
            "path": MetadataValue.path(str(path)),
        }
    )
    return str(path)


@asset_check(asset=raw_mammography_dataset)
def class_balance_check() -> AssetCheckResult:
    frame = load_dataset(get_settings().data_dir / "mammography.csv")
    positive_rate = float(frame["target"].mean())
    return AssetCheckResult(
        passed=0.001 <= positive_rate <= 0.40,
        metadata={"positive_rate": positive_rate},
    )


@asset_check(asset=deployment_manifest)
def deployment_artifacts_check() -> AssetCheckResult:
    paths = DeploymentPaths(get_settings().artifact_dir)
    missing = [
        str(path)
        for path in (paths.manifest, paths.champion_model, paths.fallback_model)
        if not path.exists()
    ]
    return AssetCheckResult(passed=not missing, metadata={"missing": missing})
