from __future__ import annotations

from pathlib import Path

import pytest

from mle_platform.monitoring.observation_store import JsonMonitoringObservationStore


def test_observations_are_safe_and_immutable(tmp_path: Path) -> None:
    store = JsonMonitoringObservationStore(tmp_path)
    first = store.write(observation_id="obs-1", payload={"decision": "healthy"})
    assert store.write(
        observation_id="obs-1", payload={"decision": "healthy"}
    ) == first
    with pytest.raises(ValueError, match="different"):
        store.write(observation_id="obs-1", payload={"decision": "investigate"})
    with pytest.raises(ValueError, match="filename-safe"):
        store.write(observation_id="../escape", payload={})
