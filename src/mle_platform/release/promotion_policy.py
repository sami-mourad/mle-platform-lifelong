"""Explicit, testable model-promotion policy."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class MetricRequirement:
    name: str
    minimum: float | None = None
    maximum: float | None = None
    maximum_regression: float | None = None
    higher_is_better: bool | None = None

    def __post_init__(self) -> None:
        if self.minimum is None and self.maximum is None:
            raise ValueError("a metric requirement needs a minimum or maximum")
        if self.maximum_regression is not None and self.maximum_regression < 0:
            raise ValueError("maximum_regression cannot be negative")
        if (
            self.maximum_regression is not None
            and self.higher_is_better is None
            and self.minimum is not None
            and self.maximum is not None
        ):
            raise ValueError(
                "higher_is_better must be explicit for bounded metrics with regression gates"
            )

    @property
    def resolved_higher_is_better(self) -> bool:
        if self.higher_is_better is not None:
            return self.higher_is_better
        return self.minimum is not None


@dataclass(frozen=True)
class PromotionDecision:
    approved: bool
    reasons: tuple[str, ...]
    evaluated_metrics: dict[str, float]


class PromotionPolicy:
    """Fail-closed metric gate with direction-aware incumbent comparisons."""

    def __init__(self, requirements: Sequence[MetricRequirement]) -> None:
        self.requirements = tuple(requirements)
        if not self.requirements:
            raise ValueError("promotion requirements cannot be empty")
        names = [requirement.name for requirement in self.requirements]
        if len(set(names)) != len(names):
            raise ValueError("promotion metric requirements must be unique")

    def evaluate(
        self,
        *,
        candidate_metrics: Mapping[str, float],
        incumbent_metrics: Mapping[str, float] | None = None,
    ) -> PromotionDecision:
        reasons: list[str] = []
        evaluated: dict[str, float] = {}
        incumbent_metrics = dict(incumbent_metrics or {})
        for requirement in self.requirements:
            if requirement.name not in candidate_metrics:
                reasons.append(f"missing required metric: {requirement.name}")
                continue
            value = float(candidate_metrics[requirement.name])
            evaluated[requirement.name] = value
            if requirement.minimum is not None and value < requirement.minimum:
                reasons.append(
                    f"{requirement.name}={value:.6g} is below minimum {requirement.minimum:.6g}"
                )
            if requirement.maximum is not None and value > requirement.maximum:
                reasons.append(
                    f"{requirement.name}={value:.6g} exceeds maximum {requirement.maximum:.6g}"
                )
            if requirement.maximum_regression is not None:
                if requirement.name not in incumbent_metrics:
                    reasons.append(
                        f"missing incumbent metric for regression gate: {requirement.name}"
                    )
                    continue
                incumbent = float(incumbent_metrics[requirement.name])
                regression = (
                    incumbent - value
                    if requirement.resolved_higher_is_better
                    else value - incumbent
                )
                if regression > requirement.maximum_regression:
                    reasons.append(
                        f"{requirement.name} regressed by {regression:.6g}; "
                        f"maximum allowed is {requirement.maximum_regression:.6g}"
                    )
        return PromotionDecision(
            approved=not reasons,
            reasons=tuple(reasons),
            evaluated_metrics=evaluated,
        )
