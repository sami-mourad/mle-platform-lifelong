"""Convert monitoring evidence into a bounded operational decision."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum


class MonitoringDecision(StrEnum):
    HEALTHY = "healthy"
    INVESTIGATE = "investigate"
    NO_DATA = "no_data"


@dataclass(frozen=True)
class MonitoringPolicy:
    minimum_current_rows: int = 20
    maximum_drifted_feature_fraction: float = 0.30
    minimum_matured_fraction: float = 0.10
    minimum_recall: float | None = None

    def evaluate(
        self,
        *,
        current_row_count: int,
        drifted_feature_count: int,
        monitored_feature_count: int,
        summary: Mapping[str, float | int | None],
    ) -> tuple[MonitoringDecision, tuple[str, ...]]:
        if current_row_count < self.minimum_current_rows:
            return MonitoringDecision.NO_DATA, (
                f"current rows {current_row_count} below {self.minimum_current_rows}",
            )
        reasons: list[str] = []
        drift_fraction = (
            drifted_feature_count / monitored_feature_count
            if monitored_feature_count
            else 1.0
        )
        if drift_fraction > self.maximum_drifted_feature_fraction:
            reasons.append(f"drifted feature fraction is {drift_fraction:.3f}")
        matured_fraction = float(summary.get("matured_fraction") or 0.0)
        if matured_fraction < self.minimum_matured_fraction:
            reasons.append(f"matured fraction is only {matured_fraction:.3f}")
        if self.minimum_recall is not None:
            recall = summary.get("recall")
            if recall is None:
                reasons.append("recall is unavailable")
            elif float(recall) < self.minimum_recall:
                reasons.append(f"recall {float(recall):.3f} below {self.minimum_recall:.3f}")
        return (
            MonitoringDecision.INVESTIGATE if reasons else MonitoringDecision.HEALTHY,
            tuple(reasons),
        )
