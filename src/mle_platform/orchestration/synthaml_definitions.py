"""Optional standalone Dagster Definitions for the SynthAML overlay."""

from __future__ import annotations

from typing import Any

_DagsterDefinitions: Any
try:
    from dagster import Definitions as _DagsterDefinitions
except ImportError:  # importing the package does not require Dagster
    _DagsterDefinitions = None

from mle_platform.orchestration.assets.synthaml_feast_materialization import (
    synthaml_feast_materialization,
)
from mle_platform.orchestration.assets.synthaml_model_release import (
    synthaml_active_release,
)
from mle_platform.orchestration.assets.synthaml_model_training import (
    synthaml_model_candidate,
)
from mle_platform.orchestration.assets.synthaml_monitoring import (
    synthaml_monitoring_observation,
)
from mle_platform.orchestration.assets.synthaml_serving_smoke import (
    synthaml_serving_smoke,
)
from mle_platform.orchestration.assets.synthaml_temporal_features import (
    synthaml_feature_snapshot,
)

SYNTHAML_ASSETS = [
    synthaml_feature_snapshot,
    synthaml_feast_materialization,
    synthaml_model_candidate,
    synthaml_active_release,
    synthaml_serving_smoke,
    synthaml_monitoring_observation,
]

definitions = (
    _DagsterDefinitions(assets=SYNTHAML_ASSETS) if _DagsterDefinitions is not None else None
)
