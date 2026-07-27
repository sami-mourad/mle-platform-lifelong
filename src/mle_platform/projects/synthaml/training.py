"""SynthAML training workflow composed from platform and temporal boundaries."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pandas as pd

from mle_platform.registry.interface import ModelRegistryPort
from mle_platform.release.promotion_policy import PromotionDecision, PromotionPolicy
from mle_platform.release.rollback import ReleaseController

from .feature_contract import SynthAMLFeatureContract


class SynthAMLTrainingService:
    def __init__(
        self,
        *,
        contract: SynthAMLFeatureContract,
        registry: ModelRegistryPort,
        promotion_policy: PromotionPolicy,
        release_controller: ReleaseController,
    ) -> None:
        self.contract = contract
        self.registry = registry
        self.promotion_policy = promotion_policy
        self.release_controller = release_controller

    def train_candidate(
        self,
        *,
        training_table: pd.DataFrame,
        target_column: str,
        output_directory: str | Path,
        decision_threshold: float,
        code_revision: str | None = None,
        run_tags: Mapping[str, str] | None = None,
    ) -> tuple[object, PromotionDecision]:
        result = self.registry.train_register_release(
            training_table=training_table,
            feature_columns=self.contract.feature_columns,
            target_column=target_column,
            feature_schema_version=self.contract.feature_schema_version,
            feature_service_name=self.contract.feature_service_name,
            output_directory=str(output_directory),
            decision_threshold=decision_threshold,
            promote_to_champion=False,
            code_revision=code_revision,
            run_tags=run_tags,
        )
        decision = self.promotion_policy.evaluate(
            candidate_metrics=result.release_manifest.metrics,
        )
        if decision.approved:
            self.release_controller.activate(result.release_manifest)
        return result, decision
