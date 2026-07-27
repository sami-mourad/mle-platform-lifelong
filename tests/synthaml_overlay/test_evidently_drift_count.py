from __future__ import annotations

import json
from pathlib import Path

import pytest

from mle_platform.monitoring.evidently import EvidentlyMonitoringAdapter


def write_report(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload))
    return path


def test_drifted_feature_count_reads_simple_named_metric(tmp_path: Path) -> None:
    report = write_report(
        tmp_path / "simple.json",
        {"metrics": [{"metric_id": "DriftedColumnsCount", "value": {"count": 3}}]},
    )
    assert EvidentlyMonitoringAdapter.drifted_feature_count(report) == 3


def test_drifted_feature_count_reads_evidently_07_count_value(tmp_path: Path) -> None:
    report = write_report(
        tmp_path / "evidently-07.json",
        {
            "metrics": [
                {
                    "metric": {
                        "type": "evidently:metric_v2:DriftedColumnsCount",
                        "drift_share": 0.5,
                    },
                    "value": {
                        "count": {"value": 2, "display_name": "Count of Drifted Columns"},
                        "share": {"value": 0.5, "display_name": "Share of Drifted Columns"},
                    },
                }
            ]
        },
    )
    assert EvidentlyMonitoringAdapter.drifted_feature_count(report) == 2


def test_drifted_feature_count_reads_nested_metric_config(tmp_path: Path) -> None:
    report = write_report(
        tmp_path / "nested-config.json",
        {
            "metrics": [
                {
                    "metric_config": {
                        "metric": {"type": "DriftedColumnsCount"},
                    },
                    "result": {"current": {"count": {"value": 1}}},
                }
            ]
        },
    )
    assert EvidentlyMonitoringAdapter.drifted_feature_count(report) == 1


def test_drifted_feature_count_reads_legacy_dataset_drift_metric(tmp_path: Path) -> None:
    report = write_report(
        tmp_path / "legacy.json",
        {
            "metrics": [
                {
                    "metric": "DatasetDriftMetric",
                    "result": {
                        "number_of_columns": 4,
                        "number_of_drifted_columns": 2,
                        "share_of_drifted_columns": 0.5,
                    },
                }
            ]
        },
    )
    assert EvidentlyMonitoringAdapter.drifted_feature_count(report) == 2


def test_drifted_feature_count_fails_closed_when_metric_is_absent(tmp_path: Path) -> None:
    report = write_report(tmp_path / "absent.json", {"metrics": []})
    with pytest.raises(ValueError, match="supported DriftedColumnsCount encoding"):
        EvidentlyMonitoringAdapter.drifted_feature_count(report)
