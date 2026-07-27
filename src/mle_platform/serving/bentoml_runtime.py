"""Cache one immutable BentoML model per release identifier."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from mle_platform.contracts.synthaml import ModelReleaseManifest


class BentoMLReleaseRuntime:
    def __init__(self, *, model_name: str = "synthaml_fraud_detector") -> None:
        try:
            from temporal_mle.platform_integration import BentoModelReleaseAdapter
        except ImportError as error:
            raise RuntimeError(
                "Repository 1 (temporal-mle) is required for the BentoML release slice."
            ) from error
        self.adapter = BentoModelReleaseAdapter(model_name=model_name)
        self._release_id: str | None = None
        self._model: Any | None = None
        self._tag: Any | None = None

    def load(self, manifest: ModelReleaseManifest) -> None:
        if self._release_id == manifest.release_id and self._model is not None:
            return
        imported = self.adapter.import_release(manifest)
        self._tag = imported.tag
        self._model = self.adapter.load_model(imported)
        self._release_id = manifest.release_id

    def predict_probability(
        self,
        *,
        manifest: ModelReleaseManifest,
        feature_values: Mapping[str, float | int | bool],
    ) -> float:
        self.load(manifest)
        assert self._model is not None
        columns = manifest.training_dataset_manifest.feature_columns
        missing = set(columns) - set(feature_values)
        extra = set(feature_values) - set(columns)
        if missing or extra:
            raise ValueError(
                f"serving feature contract mismatch; missing={sorted(missing)}, "
                f"extra={sorted(extra)}"
            )
        frame = pd.DataFrame([{name: feature_values[name] for name in columns}])
        return float(self.adapter.predict_probability(self._model, frame)[0])
