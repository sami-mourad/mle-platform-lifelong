from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from mle_platform.projects.synthaml.service import create_app
from mle_platform.serving.contracts import ScoreRequest, ScoreResponse, ServingStatus


class FakeApplication:
    def score(self, request: ScoreRequest) -> ScoreResponse:
        return ScoreResponse(
            request_id="request-1",
            entity_id=request.entity_id,
            evaluation_timestamp=request.evaluation_timestamp,
            status=ServingStatus.MANUAL_REVIEW,
            reason="test fallback",
        )


def test_health_and_prediction_transport() -> None:
    with TestClient(create_app(lambda: FakeApplication())) as client:
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 200
        response = client.post(
            "/predict",
            json={
                "entity_id": 1,
                "evaluation_timestamp": datetime(2025, 1, 1, tzinfo=UTC).isoformat(),
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "manual_review"
