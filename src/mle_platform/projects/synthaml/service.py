"""Thin FastAPI transport for the strict SynthAML serving application."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException

from mle_platform.feature_store.feast import FeastFeatureStoreAdapter
from mle_platform.release.release_manifest import AtomicReleaseManifestRepository
from mle_platform.serving.bentoml_runtime import BentoMLReleaseRuntime
from mle_platform.serving.contracts import ScoreRequest, ScoreResponse
from mle_platform.serving.feature_retrieval import FeatureRetrievalService
from mle_platform.serving.prediction_log import JsonlPredictionLog

from .feature_contract import SynthAMLFeatureContract
from .serving import SynthAMLServingApplication


@dataclass
class _ServiceState:
    application: SynthAMLServingApplication | None = None
    error: Exception | None = None


def build_default_application() -> SynthAMLServingApplication:
    contract = SynthAMLFeatureContract.read_json(
        os.environ.get(
            "SYNTHAML_FEATURE_CONTRACT_PATH",
            "contracts/synthaml/feature_contract_v3_1_1.json",
        )
    )
    feature_store = FeastFeatureStoreAdapter(
        os.environ.get("SYNTHAML_FEAST_REPO", "feature_repo")
    )
    return SynthAMLServingApplication(
        manifests=AtomicReleaseManifestRepository(
            os.environ.get(
                "SYNTHAML_RELEASE_DIR",
                ".artifacts/releases/synthaml",
            )
        ),
        features=FeatureRetrievalService(
            store=feature_store,
            feature_service_name=contract.feature_service_name,
            feature_schema_version=contract.feature_schema_version,
            feature_columns=contract.feature_columns,
            entity_join_key=contract.entity_join_key,
        ),
        runtime=BentoMLReleaseRuntime(model_name="synthaml_fraud_detector"),
        prediction_log=JsonlPredictionLog(
            os.environ.get(
                "SYNTHAML_PREDICTION_LOG",
                ".artifacts/predictions/synthaml.jsonl",
            )
        ),
    )


def create_app(
    application_factory: Callable[
        [], SynthAMLServingApplication
    ] = build_default_application,
) -> FastAPI:
    state = _ServiceState()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            state.application = application_factory()
        except Exception as error:  # readiness exposes initialization failure
            state.error = error
        yield

    app = FastAPI(
        title="SynthAML Temporal Fraud Scoring",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "live"}

    @app.get("/health/ready")
    def ready() -> dict[str, str]:
        if state.application is None:
            raise HTTPException(status_code=503, detail=str(state.error))
        return {"status": "ready"}

    @app.post("/predict", response_model=ScoreResponse)
    def predict(request: ScoreRequest) -> ScoreResponse:
        application = state.application
        if application is None:
            raise HTTPException(status_code=503, detail=str(state.error))
        return application.score(request)

    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run(
        "mle_platform.projects.synthaml.service:app",
        host=os.environ.get("API_HOST", "0.0.0.0"),
        port=int(os.environ.get("API_PORT", "8000")),
    )


if __name__ == "__main__":
    main()
