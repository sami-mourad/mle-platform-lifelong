from pathlib import Path

from mle_platform.model_runtime import ResilientModelRuntime


def test_rules_fallback_when_no_models_exist(tmp_path: Path) -> None:
    runtime = ResilientModelRuntime(tmp_path)
    result = runtime.predict({"attr1": 0.2})
    assert result.model_source == "rules"
    assert result.decision == "review"
    assert result.degraded is True
