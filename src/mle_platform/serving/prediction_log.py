"""Append-only local prediction log with durable line writes."""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

from mle_platform.contracts.synthaml import PredictionTraceContract


class JsonlPredictionLog:
    """Local demo implementation; replace with PostgreSQL behind the same API."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: PredictionTraceContract) -> None:
        payload = (event.model_dump_json() + "\n").encode("utf-8")
        descriptor = os.open(
            self.path,
            os.O_APPEND | os.O_CREAT | os.O_WRONLY,
            0o600,
        )
        try:
            os.write(descriptor, payload)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def read_all(self) -> list[PredictionTraceContract]:
        if not self.path.exists():
            return []
        return [
            PredictionTraceContract.model_validate_json(line)
            for line in self.path.read_text().splitlines()
            if line.strip()
        ]

    def extend(self, events: Iterable[PredictionTraceContract]) -> None:
        for event in events:
            self.append(event)
