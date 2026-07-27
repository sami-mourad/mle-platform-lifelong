from pathlib import Path

from mle_platform.io import atomic_write_json, read_json


def test_atomic_json_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    atomic_write_json(path, {"release_id": "1"})
    assert read_json(path) == {"release_id": "1"}
