from __future__ import annotations

from pathlib import Path

from mle_platform.projects.synthaml.thin_slice import run

ROOT = Path(__file__).parents[2]


def test_dependency_light_hosting_journey(tmp_path: Path) -> None:
    evidence = run(
        tmp_path,
        contract_path=ROOT / "contracts/synthaml/feature_contract_v3_1_1.json",
    )
    assert evidence["active_release_id"] == "synthaml-thin-slice-v1"
    assert evidence["scored_response"]["status"] == "scored"
    assert evidence["manual_review_response"]["status"] == "manual_review"
    assert evidence["prediction_trace_count"] == 1

    repeated = run(
        tmp_path,
        contract_path=ROOT / "contracts/synthaml/feature_contract_v3_1_1.json",
    )
    assert repeated["active_release_id"] == "synthaml-thin-slice-v1"
    assert repeated["prediction_trace_count"] == 1
