"""Platform-wide contracts and SynthAML contract package.

This package replaces the former ``mle_platform.contracts`` module so generic
platform contracts and project-specific submodules can coexist under one stable
import namespace.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DeploymentPaths:
    root: Path

    @property
    def manifest(self) -> Path:
        return self.root / "deployment_manifest.json"

    @property
    def champion_model(self) -> Path:
        return self.root / "champion.joblib"

    @property
    def fallback_model(self) -> Path:
        return self.root / "fallback.joblib"

    @property
    def evaluation_report(self) -> Path:
        return self.root / "evaluation_report.json"


@dataclass(frozen=True)
class PredictionResult:
    score: float
    decision: str
    model_source: str
    model_name: str
    model_version: str
    threshold: float
    degraded: bool
    reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "decision": self.decision,
            "model_source": self.model_source,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "threshold": self.threshold,
            "degraded": self.degraded,
            "reason": self.reason,
        }


__all__ = ["DeploymentPaths", "PredictionResult"]
