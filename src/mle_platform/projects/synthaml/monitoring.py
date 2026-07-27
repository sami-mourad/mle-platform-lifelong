"""Scheduled monitoring workflow for delayed SynthAML outcomes."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from mle_platform.monitoring.delayed_labels import DelayedLabelPopulationBuilder
from mle_platform.monitoring.evidently import EvidentlyMonitoringAdapter
from mle_platform.monitoring.monitoring_policy import MonitoringPolicy
from mle_platform.monitoring.observation_store import JsonMonitoringObservationStore


class SynthAMLMonitoringService:
    def __init__(
        self,
        *,
        policy: MonitoringPolicy,
        observation_store: JsonMonitoringObservationStore,
    ) -> None:
        self.policy = policy
        self.observation_store = observation_store
        self.evidently = EvidentlyMonitoringAdapter()

    def run(
        self,
        *,
        reference_predictions: pd.DataFrame,
        current_predictions: pd.DataFrame,
        reference_labels: pd.DataFrame,
        current_labels: pd.DataFrame,
        monitoring_cutoff: object,
        feature_columns: Sequence[str],
        output_directory: str | Path,
        model_id: str,
        observation_id: str,
    ) -> Path:
        reference = DelayedLabelPopulationBuilder.prepare_population(
            predictions=reference_predictions,
            labels=reference_labels,
            monitoring_cutoff=monitoring_cutoff,
        )
        current = DelayedLabelPopulationBuilder.prepare_population(
            predictions=current_predictions,
            labels=current_labels,
            monitoring_cutoff=monitoring_cutoff,
        )
        reports = self.evidently.run(
            reference_population=reference,
            current_population=current,
            feature_columns=feature_columns,
            output_directory=output_directory,
            model_id=model_id,
            reference_id="approved_reference_population",
        )
        summary = DelayedLabelPopulationBuilder.summary(current)
        drifted_feature_count = self.evidently.drifted_feature_count(
            reports["drift_json"]
        )
        decision, reasons = self.policy.evaluate(
            current_row_count=len(current),
            drifted_feature_count=drifted_feature_count,
            monitored_feature_count=len(feature_columns),
            summary=summary,
        )
        payload = {
            "observation_id": observation_id,
            "model_id": model_id,
            "decision": decision.value,
            "reasons": list(reasons),
            "summary": summary,
            "drifted_feature_count": drifted_feature_count,
            "monitored_feature_count": len(feature_columns),
            "reports": {name: str(path) for name, path in reports.items()},
        }
        return self.observation_store.write(
            observation_id=observation_id,
            payload=payload,
        )
