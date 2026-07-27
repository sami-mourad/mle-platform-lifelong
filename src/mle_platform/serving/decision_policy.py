"""Decision semantics stored with and derived from the immutable release."""

from __future__ import annotations

from dataclasses import dataclass

from mle_platform.contracts.synthaml import ModelReleaseManifest


@dataclass(frozen=True)
class DecisionResult:
    probability: float
    threshold: float
    predicted_positive: bool


class ReleaseDecisionPolicy:
    @staticmethod
    def decide(*, probability: float, manifest: ModelReleaseManifest) -> DecisionResult:
        probability = float(probability)
        if not 0.0 <= probability <= 1.0:
            raise ValueError("probability must be in [0, 1]")
        threshold = float(manifest.decision_threshold)
        return DecisionResult(
            probability=probability,
            threshold=threshold,
            predicted_positive=probability >= threshold,
        )
