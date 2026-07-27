from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from mle_platform.monitoring.monitoring_policy import MonitoringPolicy
from mle_platform.monitoring.observation_store import (
    JsonMonitoringObservationStore,
)
from mle_platform.projects.synthaml import SynthAMLMonitoringService

pytest.importorskip("evidently")

pytestmark = pytest.mark.integration


def prediction_frame(start: int, count: int) -> pd.DataFrame:
    base = datetime(2025, 1, 1, tzinfo=UTC)
    rows: list[dict[str, object]] = []
    for index in range(start, start + count):
        probability = 0.1 + 0.8 * ((index % 10) / 9)
        rows.append(
            {
                "sample_id": f"sample-{index}",
                "fraud_probability": probability,
                "decision": probability >= 0.5,
                "feature_a": float(index % 7),
                "feature_b": float((index % 5) - 2),
                "evaluation_timestamp": base + timedelta(hours=index),
            }
        )
    return pd.DataFrame(rows)


def labels(
    predictions: pd.DataFrame,
    cutoff: datetime,
    pending_tail: int = 0,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    row_count = len(predictions)
    for position, row in predictions.reset_index(drop=True).iterrows():
        mature = position < row_count - pending_tail
        rows.append(
            {
                "sample_id": row["sample_id"],
                "label_value": (
                    "Reported"
                    if row["fraud_probability"] >= 0.55
                    else "Dismissed"
                ),
                "label_available_timestamp": (
                    cutoff - timedelta(hours=1)
                    if mature
                    else cutoff + timedelta(days=1)
                ),
            }
        )
    return pd.DataFrame(rows)


def test_monitoring_reports_pending_labels_and_persists_observation(
    tmp_path: Path,
) -> None:
    cutoff = datetime(2025, 2, 1, tzinfo=UTC)
    reference = prediction_frame(0, 30)
    current = prediction_frame(30, 30)
    service = SynthAMLMonitoringService(
        policy=MonitoringPolicy(
            minimum_current_rows=20,
            minimum_matured_fraction=0.5,
        ),
        observation_store=JsonMonitoringObservationStore(
            tmp_path / "observations"
        ),
    )
    observation = service.run(
        reference_predictions=reference,
        current_predictions=current,
        reference_labels=labels(reference, cutoff),
        current_labels=labels(current, cutoff, pending_tail=5),
        monitoring_cutoff=cutoff,
        feature_columns=("feature_a", "feature_b"),
        output_directory=tmp_path / "reports",
        model_id="model:1",
        observation_id="obs-1",
    )
    payload = json.loads(observation.read_text())
    assert payload["summary"]["prediction_count"] == 30
    assert payload["summary"]["pending_prediction_count"] == 5
    assert Path(payload["reports"]["drift_html"]).exists()
    assert Path(payload["reports"]["performance_html"]).exists()
