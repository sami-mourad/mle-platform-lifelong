"""Atomic file-system authority for the active immutable release manifest."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from mle_platform.contracts.synthaml import ModelReleaseManifest


class AtomicReleaseManifestRepository:
    """Publish immutable history first, then atomically replace the active pointer."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.history = self.root / "history"
        self.active = self.root / "active_release.json"
        self.root.mkdir(parents=True, exist_ok=True)
        self.history.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _digest(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    def _release_path(self, release_id: str) -> Path:
        if not release_id or Path(release_id).name != release_id:
            raise ValueError("release_id must be a safe filename component")
        return self.history / f"{release_id}.json"

    def publish(self, manifest: ModelReleaseManifest) -> Path:
        payload = manifest.model_dump_json(indent=2).encode("utf-8")
        immutable = self._release_path(manifest.release_id)
        if immutable.exists():
            if immutable.read_bytes() != payload:
                raise ValueError("release_id already exists with different content")
        else:
            temporary_history = immutable.with_suffix(".json.tmp")
            temporary_history.write_bytes(payload)
            os.replace(temporary_history, immutable)

        pointer = {
            "release_id": manifest.release_id,
            "manifest_path": str(immutable.relative_to(self.root)),
            "manifest_sha256": self._digest(payload),
            "published_timestamp": datetime.now(UTC).isoformat(),
        }
        temporary_active = self.active.with_suffix(".json.tmp")
        temporary_active.write_text(json.dumps(pointer, indent=2))
        os.replace(temporary_active, self.active)
        return self.active

    def load_active(self) -> ModelReleaseManifest:
        if not self.active.exists():
            raise FileNotFoundError("no active release manifest has been published")
        pointer = json.loads(self.active.read_text())
        stored = Path(pointer["manifest_path"])
        path = stored if stored.is_absolute() else self.root / stored
        payload = path.read_bytes()
        if self._digest(payload) != pointer["manifest_sha256"]:
            raise ValueError("active release manifest checksum mismatch")
        manifest = ModelReleaseManifest.model_validate_json(payload)
        if manifest.release_id != pointer["release_id"]:
            raise ValueError("active pointer release_id does not match manifest")
        return manifest

    def load_release(self, release_id: str) -> ModelReleaseManifest:
        path = self._release_path(release_id)
        if not path.exists():
            raise FileNotFoundError(f"unknown release_id: {release_id}")
        return ModelReleaseManifest.model_validate_json(path.read_text())
