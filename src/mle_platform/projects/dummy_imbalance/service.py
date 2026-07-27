from __future__ import annotations

import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from mle_platform.config import get_settings
from mle_platform.logging import configure_logging
from mle_platform.model_runtime import ResilientModelRuntime
from mle_platform.projects.dummy_imbalance.schemas import (
    ReadinessResponse,
    ScoreRequest,
    ScoreResponse,
)

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)
runtime = ResilientModelRuntime(settings.artifact_dir, settings.model_refresh_seconds)

PREDICTIONS = Counter(
    "mle_predictions_total",
    "Predictions emitted by model source and decision",
    ["model_source", "decision"],
)
LATENCY = Histogram(
    "mle_prediction_latency_seconds",
    "End-to-end prediction latency",
    buckets=(0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)
FALLBACKS = Counter(
    "mle_fallback_total",
    "Fallback invocations by source and reason",
    ["model_source", "reason"],
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    runtime.refresh(force=True)
    yield


app = FastAPI(
    title="Dummy Imbalanced Risk Service",
    version="0.1.0",
    description="Champion/fallback/rules deployment example for the reusable MLE platform.",
    lifespan=lifespan,
)


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "live"}


@app.get("/health/ready", response_model=ReadinessResponse)
def ready() -> ReadinessResponse:
    return ReadinessResponse(
        status="ready" if runtime.ready else "degraded-rules-only",
        learned_model_loaded=runtime.ready,
        release_id=runtime.release_id,
    )


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/v1/score", response_model=ScoreResponse)
def score(
    request: ScoreRequest,
    x_request_id: Annotated[str | None, Header()] = None,
    x_force_fallback: Annotated[bool | None, Header()] = None,
) -> ScoreResponse:
    request_id = x_request_id or str(uuid.uuid4())
    force_fallback = bool(x_force_fallback)
    if force_fallback and not settings.allow_dev_force_fallback:
        raise HTTPException(status_code=403, detail="Forced fallback is disabled")
    started = time.perf_counter()
    try:
        result = runtime.predict(request.features, force_fallback=force_fallback)
        PREDICTIONS.labels(result.model_source, result.decision).inc()
        if result.degraded:
            FALLBACKS.labels(result.model_source, result.reason or "unspecified").inc()
        logger.info(
            "Prediction completed",
            extra={
                "request_id": request_id,
                "model_source": result.model_source,
                "model_version": result.model_version,
                "decision": result.decision,
            },
        )
        return ScoreResponse(request_id=request_id, **result.as_dict())
    finally:
        LATENCY.observe(time.perf_counter() - started)


def main() -> None:
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)


if __name__ == "__main__":
    main()
