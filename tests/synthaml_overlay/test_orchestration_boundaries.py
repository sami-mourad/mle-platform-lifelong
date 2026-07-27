from __future__ import annotations

from mle_platform.orchestration.assets.synthaml_model_release import (
    synthaml_active_release,
)
from mle_platform.orchestration.assets.synthaml_serving_smoke import (
    synthaml_serving_smoke,
)
from mle_platform.orchestration.synthaml_definitions import SYNTHAML_ASSETS


class Decision:
    approved = True
    reasons: tuple[str, ...] = ()


class Manifest:
    release_id = "r1"


class Result:
    release_manifest = Manifest()


class Response:
    reason = None

    class Status:
        value = "scored"

    status = Status()

    @staticmethod
    def model_dump(*, mode: str) -> dict[str, object]:
        assert mode == "json"
        return {"status": "scored", "release_id": "r1"}


class Application:
    @staticmethod
    def score(request: object) -> Response:
        assert request == "known-request"
        return Response()


def test_synthaml_asset_functions_import_without_dagster() -> None:
    assert len(SYNTHAML_ASSETS) == 6
    assert synthaml_active_release((Result(), Decision())) == "r1"
    assert synthaml_serving_smoke(Application(), "known-request")["status"] == "scored"
