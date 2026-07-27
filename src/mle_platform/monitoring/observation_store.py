"""Atomic immutable local observation store for monitoring decisions."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class JsonMonitoringObservationStore:
    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_id(observation_id: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9._-]+", observation_id):
            raise ValueError("observation_id must be filename-safe")
        return observation_id

    def write(self, *, observation_id: str, payload: Mapping[str, Any]) -> Path:
        safe_id = self._safe_id(observation_id)
        destination = self.directory / f"{safe_id}.json"
        serialized = json.dumps(dict(payload), indent=2, sort_keys=True, default=str)
        if destination.exists():
            if destination.read_text() != serialized:
                raise ValueError(
                    "observation_id already exists with different monitoring evidence"
                )
            return destination
        temporary = destination.with_suffix(".json.tmp")
        temporary.write_text(serialized)
        os.replace(temporary, destination)
        return destination
