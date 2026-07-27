from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from mle_platform.contracts import DeploymentPaths, PredictionResult
from mle_platform.io import read_json

logger = logging.getLogger(__name__)


@dataclass
class LoadedBundle:
    champion: Any | None
    fallback: Any | None
    manifest: dict[str, Any]
    manifest_mtime: float


class ResilientModelRuntime:
    """Loads deployment artifacts and executes a three-level fallback chain.

    This runtime treats the deployment manifest as the atomic release pointer.
    Model files are written first; the manifest is replaced last. Readers therefore
    never observe a manifest that points to partially copied artifacts.
    """

    def __init__(self, artifact_dir: Path, refresh_seconds: int = 5) -> None:
        self.paths = DeploymentPaths(artifact_dir)
        self.refresh_seconds = refresh_seconds
        self._lock = threading.RLock()
        self._bundle = LoadedBundle(None, None, {}, -1.0)
        self._last_refresh = 0.0
        self.refresh(force=True)

    def refresh(self, force: bool = False) -> None:
        now = time.monotonic()
        if not force and now - self._last_refresh < self.refresh_seconds:
            return
        self._last_refresh = now
        if not self.paths.manifest.exists():
            return
        manifest_mtime = self.paths.manifest.stat().st_mtime
        if manifest_mtime == self._bundle.manifest_mtime:
            return
        try:
            manifest = read_json(self.paths.manifest)
            champion = joblib.load(self.paths.champion_model)
            fallback = joblib.load(self.paths.fallback_model)
            with self._lock:
                self._bundle = LoadedBundle(champion, fallback, manifest, manifest_mtime)
            logger.info(
                "Reloaded deployment manifest", extra={"model_version": manifest.get("release_id")}
            )
        except Exception:
            logger.exception("Model refresh failed; retaining last known good bundle")

    @property
    def ready(self) -> bool:
        with self._lock:
            return self._bundle.champion is not None or self._bundle.fallback is not None

    @property
    def release_id(self) -> str:
        with self._lock:
            return str(self._bundle.manifest.get("release_id", "rules-only"))

    def predict(self, features: dict[str, float], force_fallback: bool = False) -> PredictionResult:
        self.refresh()
        with self._lock:
            bundle = self._bundle
        required_features = list(bundle.manifest.get("feature_names", sorted(features)))
        missing = [name for name in required_features if name not in features]
        if missing:
            return self._rules_fallback(features, f"missing_features:{','.join(missing)}")
        frame = pd.DataFrame(
            [[features[name] for name in required_features]], columns=required_features
        )

        if not force_fallback and bundle.champion is not None:
            try:
                return self._model_prediction(bundle.champion, frame, bundle.manifest, "champion")
            except Exception:
                logger.exception("Champion inference failed; trying packaged fallback")

        if bundle.fallback is not None:
            try:
                return self._model_prediction(bundle.fallback, frame, bundle.manifest, "fallback")
            except Exception:
                logger.exception("Fallback model inference failed; using conservative policy")

        return self._rules_fallback(features, "all_models_unavailable")

    @staticmethod
    def _model_prediction(
        model: Any,
        frame: pd.DataFrame,
        manifest: dict[str, Any],
        source: str,
    ) -> PredictionResult:
        score = float(np.asarray(model.predict_proba(frame))[0, 1])
        model_record = manifest[source]
        threshold = float(model_record["threshold"])
        decision = "review" if score >= threshold else "clear"
        return PredictionResult(
            score=score,
            decision=decision,
            model_source=source,
            model_name=str(model_record["name"]),
            model_version=str(model_record.get("version", "local")),
            threshold=threshold,
            degraded=source != "champion",
            reason=None if source == "champion" else "champion_unavailable_or_forced",
        )

    @staticmethod
    def _rules_fallback(features: dict[str, float], reason: str) -> PredictionResult:
        # A true fail-safe policy: when the model plane is unavailable, route to
        # manual review rather than silently approving a risk-sensitive decision.
        # The score is deliberately not presented as a learned probability.
        finite_values = [float(value) for value in features.values() if np.isfinite(value)]
        heuristic = float(np.mean(np.abs(finite_values))) if finite_values else 1.0
        score = min(1.0, heuristic / (1.0 + heuristic))
        return PredictionResult(
            score=score,
            decision="review",
            model_source="rules",
            model_name="conservative_manual_review",
            model_version="1",
            threshold=0.0,
            degraded=True,
            reason=reason,
        )
