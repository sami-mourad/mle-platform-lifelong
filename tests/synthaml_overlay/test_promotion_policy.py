from mle_platform.release.promotion_policy import MetricRequirement, PromotionPolicy


def test_promotion_policy_pass_and_fail() -> None:
    policy = PromotionPolicy([
        MetricRequirement("validation_f1", minimum=0.60, maximum_regression=0.05),
        MetricRequirement("validation_brier_score", maximum=0.25),
    ])
    approved = policy.evaluate(
        candidate_metrics={"validation_f1": 0.70, "validation_brier_score": 0.18},
        incumbent_metrics={"validation_f1": 0.72},
    )
    assert approved.approved

    rejected = policy.evaluate(
        candidate_metrics={"validation_f1": 0.60, "validation_brier_score": 0.40},
        incumbent_metrics={"validation_f1": 0.72},
    )
    assert not rejected.approved
    assert len(rejected.reasons) == 2


def test_lower_is_better_regression_is_direction_aware() -> None:
    policy = PromotionPolicy([
        MetricRequirement(
            "validation_brier_score",
            maximum=0.30,
            maximum_regression=0.02,
        )
    ])
    rejected = policy.evaluate(
        candidate_metrics={"validation_brier_score": 0.24},
        incumbent_metrics={"validation_brier_score": 0.20},
    )
    assert not rejected.approved
    assert "regressed" in rejected.reasons[0]


def test_regression_gate_requires_incumbent_evidence() -> None:
    policy = PromotionPolicy([
        MetricRequirement("validation_f1", minimum=0.5, maximum_regression=0.05)
    ])
    decision = policy.evaluate(candidate_metrics={"validation_f1": 0.8})
    assert not decision.approved
    assert "missing incumbent" in decision.reasons[0]
