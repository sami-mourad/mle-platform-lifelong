"""Optional standalone Dagster Definitions for the SynthAML overlay."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any, cast

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

_DefinitionsFactory = Callable[..., Any]


def _load_definitions_factory() -> _DefinitionsFactory | None:
    """Load compatible Dagster Definitions only when available."""
    try:
        dagster_module = import_module("dagster")
    except ImportError:
        return None

    definitions_factory = getattr(
        dagster_module,
        "Definitions",
        None,
    )
    if definitions_factory is None:
        return None

    return cast(
        _DefinitionsFactory,
        definitions_factory,
    )


SYNTHAML_ASSETS = [
    synthaml_feature_snapshot,
    synthaml_feast_materialization,
    synthaml_model_candidate,
    synthaml_active_release,
    synthaml_serving_smoke,
    synthaml_monitoring_observation,
]

_definitions_factory = _load_definitions_factory()

definitions = (
    _definitions_factory(assets=SYNTHAML_ASSETS) if _definitions_factory is not None else None
)
