from fastapi.testclient import TestClient

from mle_platform.projects.dummy_imbalance.service import app


def test_liveness_contract() -> None:
    response = TestClient(app).get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "live"}


def test_score_contract_degrades_safely_without_artifacts() -> None:
    response = TestClient(app).post("/v1/score", json={"features": {"attr1": 0.5}})
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "review"
    assert payload["model_source"] in {"champion", "fallback", "rules"}
    assert isinstance(payload["request_id"], str)
