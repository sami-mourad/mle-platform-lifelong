"""Verify the Repository-1 / Repository-2 SynthAML wire boundary."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast


def _load_json_object(path: Path) -> dict[str, object]:
    payload: Any = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return cast(dict[str, object], payload)


def _project_version(repo: Path) -> str | None:
    payload = tomllib.loads((repo / "pyproject.toml").read_text())
    project = payload.get("project")
    if isinstance(project, Mapping):
        version = project.get("version")
        if version is not None:
            return str(version)

    tool = payload.get("tool")
    if isinstance(tool, Mapping):
        poetry = tool.get("poetry")
        if isinstance(poetry, Mapping):
            version = poetry.get("version")
            if version is not None:
                return str(version)
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-1", type=Path, required=True)
    parser.add_argument(
        "--feature-contract",
        type=Path,
        default=Path(
            "contracts/synthaml/feature_contract_v3_1_1.json"
        ),
    )
    parser.add_argument("--feature-snapshot", type=Path)
    args = parser.parse_args()

    repo1 = args.repository_1.resolve()
    repo2 = Path(__file__).parents[1].resolve()
    sys.path.insert(0, str(repo2 / "src"))
    contract_path = (repo2 / args.feature_contract).resolve()
    issues: list[str] = []
    snapshot_summary: dict[str, object] | None = None
    contract = _load_json_object(contract_path)

    if not repo1.is_dir() or not (repo1 / "pyproject.toml").is_file():
        issues.append(f"Repository-1 checkout is invalid: {repo1}")
    else:
        expected_version = contract.get("temporal_package_version")
        observed_version = _project_version(repo1)
        if observed_version != expected_version:
            issues.append(
                "Repository-1 package version mismatch: "
                f"expected {expected_version!r}, observed {observed_version!r}"
            )

        schema_names = [
            "feature_snapshot_v3_1.schema.json",
            "training_dataset_v1.schema.json",
            "model_release_v1.schema.json",
            "prediction_event_v1.schema.json",
            "prediction_trace_v1.schema.json",
            "label_event_v1.schema.json",
        ]
        for name in schema_names:
            left = repo1 / "contracts" / name
            right = repo2 / "contracts" / "synthaml" / name
            if not left.exists() or not right.exists():
                issues.append(f"missing shared schema: {name}")
            elif _load_json_object(left) != _load_json_object(right):
                issues.append(f"shared schema drift: {name}")

    if args.feature_snapshot is not None:
        snapshot_path = args.feature_snapshot.resolve()
        if not snapshot_path.is_file():
            issues.append(f"feature snapshot does not exist: {snapshot_path}")
        else:
            from mle_platform.projects.synthaml.adapter import (
                TemporalMLEProjectAdapter,
            )
            from mle_platform.projects.synthaml.feature_contract import (
                SynthAMLFeatureContract,
            )

            model_contract = SynthAMLFeatureContract.read_json(contract_path)
            snapshot = TemporalMLEProjectAdapter(
                model_contract
            ).load_feature_snapshot(snapshot_path)
            snapshot_summary = {
                "path": str(snapshot_path),
                "row_count": len(snapshot),
                "feature_count": len(model_contract.feature_columns),
                "feature_columns": list(model_contract.feature_columns),
                "feature_schema_versions": sorted(
                    snapshot["feature_schema_version"]
                    .astype(str)
                    .unique()
                    .tolist()
                ),
            }

    report = {
        "passes_cross_repository_contract": not issues,
        "issues": issues,
        "repository_1": str(repo1),
        "feature_contract": str(contract_path),
        "snapshot": snapshot_summary,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(1 if issues else 0)


if __name__ == "__main__":
    main()
