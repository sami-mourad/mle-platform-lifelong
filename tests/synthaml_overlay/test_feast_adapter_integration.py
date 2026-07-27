from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from mle_platform.feature_store.feast import FeastFeatureStoreAdapter
from mle_platform.feature_store.interface import (
    HistoricalFeatureRequest,
    OnlineFeatureRequest,
)
from mle_platform.projects.synthaml import SynthAMLFeatureContract

pl = pytest.importorskip("polars")
pytest.importorskip("feast")

pytestmark = pytest.mark.integration


def test_feast_historical_materialization_and_online_parity(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "feature_repo"
    repo.mkdir()
    (repo / "data").mkdir()
    feature_path = tmp_path / "features.parquet"
    pl.DataFrame(
        {
            "AlertID": [1, 1, 2, 2],
            "evaluation_timestamp": [
                datetime(2025, 1, 1, tzinfo=UTC),
                datetime(2025, 1, 2, tzinfo=UTC),
                datetime(2025, 1, 1, tzinfo=UTC),
                datetime(2025, 1, 2, tzinfo=UTC),
            ],
            "transaction_count": [2.0, 3.0, 5.0, 7.0],
            "absolute_transaction_amount_flow": [10.0, 12.0, 20.0, 22.0],
            "recent_acceleration": [-1.0, 0.5, 1.0, 2.0],
        }
    ).write_parquet(feature_path)
    (repo / "feature_store.yaml").write_text(
        "\n".join(
            [
                "project: lifelong_synthaml_overlay_test",
                "registry: data/registry.db",
                "provider: local",
                "offline_store:",
                "  type: file",
                "online_store:",
                "  type: sqlite",
                "  path: data/online.db",
                "entity_key_serialization_version: 3",
            ]
        )
    )
    contract = SynthAMLFeatureContract(
        contract_version="v1",
        temporal_package_version="3.1.1",
        feature_schema_version="temporal_feature_schema_v3_1",
        feature_service_name="service_v1",
        feature_view_name="view_v1",
        entity_name="alert",
        entity_join_key="AlertID",
        event_timestamp_column="evaluation_timestamp",
        feature_columns=(
            "transaction_count",
            "absolute_transaction_amount_flow",
            "recent_acceleration",
        ),
        feature_dtypes={
            "transaction_count": "FLOAT64",
            "absolute_transaction_amount_flow": "FLOAT64",
            "recent_acceleration": "FLOAT64",
        },
    )
    objects = contract.feast_objects(parquet_path=str(feature_path))
    adapter = FeastFeatureStoreAdapter(str(repo))
    adapter.apply(
        [
            objects["entity"],
            objects["source"],
            objects["feature_view"],
            objects["feature_service"],
        ]
    )

    historical = adapter.historical_features(
        HistoricalFeatureRequest(
            entity_dataframe=pl.DataFrame(
                {
                    "AlertID": [1, 2],
                    "event_timestamp": [
                        datetime(2025, 1, 1, 12, tzinfo=UTC),
                        datetime(2025, 1, 1, 12, tzinfo=UTC),
                    ],
                }
            ).to_pandas(),
            feature_service_name="service_v1",
        )
    )
    historical_frame = pl.from_arrow(historical).sort("AlertID")
    count_name = next(
        column for column in historical_frame.columns if column.endswith("__transaction_count")
    )
    assert historical_frame[count_name].to_list() == [2.0, 5.0]

    adapter.materialize(
        start=datetime(2024, 12, 31, tzinfo=UTC),
        end=datetime(2025, 1, 3, tzinfo=UTC),
    )
    online = adapter.online_features(
        OnlineFeatureRequest(
            entity_rows=({"AlertID": 1}, {"AlertID": 2}),
            feature_service_name="service_v1",
        )
    )
    latest = adapter.historical_features(
        HistoricalFeatureRequest(
            entity_dataframe=pl.DataFrame(
                {
                    "AlertID": [1, 2],
                    "event_timestamp": [
                        datetime(2025, 1, 2, tzinfo=UTC),
                        datetime(2025, 1, 2, tzinfo=UTC),
                    ],
                }
            ).to_pandas(),
            feature_service_name="service_v1",
        )
    )
    parity = adapter.parity_report(
        historical_table=latest,
        online_features=online,
        entity_column="AlertID",
        feature_columns=contract.feature_columns,
    )
    assert parity.height == 6
    assert parity["passes_parity"].all()
