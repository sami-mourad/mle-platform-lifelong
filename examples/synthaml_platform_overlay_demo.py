"""Bounded MLflow release proof for synthetic data or a Repository-1 snapshot."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

from mle_platform.projects.synthaml import (
    SynthAMLFeatureContract,
    SynthAMLTrainingService,
    TemporalMLEProjectAdapter,
)
from mle_platform.registry.mlflow import MLflowRegistryAdapter
from mle_platform.release.promotion_policy import MetricRequirement, PromotionPolicy
from mle_platform.release.release_manifest import AtomicReleaseManifestRepository
from mle_platform.release.rollback import ReleaseController


def synthetic_training_table() -> pd.DataFrame:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    rows: list[dict[str, object]] = []
    for index in range(80):
        count = float(1 + index % 7)
        flow = float((index % 9) * count)
        interarrival_mean = float(60 + (index % 5) * 30)
        label = int((count >= 5 and flow > 12) or interarrival_mean > 150)
        rows.append(
            {
                "AlertID": index + 1,
                "evaluation_timestamp": start + timedelta(hours=index),
                "transaction_count": count,
                "absolute_transaction_amount_flow": flow,
                "interarrival_time_mean_seconds": interarrival_mean,
                "feature_schema_version": "temporal_feature_schema_v3_1",
                "target": label,
            }
        )
    return pd.DataFrame(rows)


def _binary_target(
    table: pd.DataFrame,
    *,
    source_column: str,
    positive_label: str | None,
    negative_label: str | None,
) -> pd.DataFrame:
    result = table.copy()
    observed = result[source_column].dropna()
    if positive_label is None:
        unique = sorted(observed.unique().tolist())
        if len(unique) != 2 or not all(value in (0, 1, False, True) for value in unique):
            raise ValueError(
                "non-binary-text targets require --positive-label and --negative-label"
            )
        result["target"] = result[source_column].astype(int)
        return result
    if negative_label is None:
        raise ValueError("--negative-label is required with --positive-label")
    selected = result[source_column].astype(str).isin([positive_label, negative_label])
    result = result.loc[selected].copy()
    if result.empty:
        raise ValueError("no rows match the requested positive/negative labels")
    result["target"] = (result[source_column].astype(str) == positive_label).astype(int)
    if result["target"].nunique() != 2:
        raise ValueError("the selected mature population does not contain both target classes")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--feature-snapshot", type=Path)
    parser.add_argument("--target-column", default="target")
    parser.add_argument("--positive-label")
    parser.add_argument("--negative-label")
    parser.add_argument("--label-available-timestamp-column")
    parser.add_argument("--maturity-cutoff")
    parser.add_argument("--decision-threshold", type=float, default=0.5)
    args = parser.parse_args()

    output = args.output_directory.resolve()
    output.mkdir(parents=True, exist_ok=True)
    contract = SynthAMLFeatureContract.read_json(
        Path(__file__).parents[1] / "contracts/synthaml/feature_contract_v3_1_1.json"
    )
    adapter = TemporalMLEProjectAdapter(contract)

    if args.feature_snapshot is None:
        table = adapter.validate_feature_snapshot(synthetic_training_table())
        source_snapshot = output / "synthetic_feature_snapshot.parquet"
        table.to_parquet(source_snapshot, index=False)
        target_column = "target"
        source_kind = "bounded_synthetic_fixture"
    else:
        source_snapshot = args.feature_snapshot.resolve()
        snapshot = adapter.load_feature_snapshot(source_snapshot)
        table = adapter.training_table(
            snapshot=snapshot,
            target_column=args.target_column,
            label_available_timestamp_column=args.label_available_timestamp_column,
            maturity_cutoff=args.maturity_cutoff,
        )
        table = _binary_target(
            table,
            source_column=args.target_column,
            positive_label=args.positive_label,
            negative_label=args.negative_label,
        )
        target_column = "target"
        source_kind = "repository_1_feature_snapshot"

    registry = MLflowRegistryAdapter(
        tracking_uri=f"sqlite:///{output / 'mlflow.db'}",
        artifact_root=output / "mlflow_artifacts",
        experiment_name="synthaml_overlay_demo",
        registered_model_name="synthaml_fraud_detector_overlay",
    )
    manifests = AtomicReleaseManifestRepository(output / "releases")
    controller = ReleaseController(registry=registry, manifests=manifests)
    training = SynthAMLTrainingService(
        contract=contract,
        registry=registry,
        promotion_policy=PromotionPolicy(
            [
                MetricRequirement("validation_f1", minimum=0.0),
                MetricRequirement(
                    "validation_brier_score",
                    maximum=1.0,
                    higher_is_better=False,
                ),
            ]
        ),
        release_controller=controller,
    )
    result, decision = training.train_candidate(
        training_table=table,
        target_column=target_column,
        output_directory=output / "training",
        decision_threshold=args.decision_threshold,
        code_revision="repo2-synthaml-demo",
        run_tags={"source_kind": source_kind},
    )
    if not decision.approved:
        raise RuntimeError(decision.reasons)

    summary = {
        "source_kind": source_kind,
        "source_snapshot": str(source_snapshot),
        "training_row_count": len(table),
        "positive_count": int(table[target_column].sum()),
        "negative_count": int((table[target_column] == 0).sum()),
        "release_id": result.release_manifest.release_id,
        "model_version": result.release_manifest.model_version,
        "active_release": manifests.load_active().release_id,
        "metrics": result.release_manifest.metrics,
        "feature_schema_version": contract.feature_schema_version,
        "feature_columns": list(contract.feature_columns),
    }
    manifest = output / "overlay_demo_manifest.json"
    manifest.write_text(json.dumps(summary, indent=2, sort_keys=True))
    print(manifest)


if __name__ == "__main__":
    main()
