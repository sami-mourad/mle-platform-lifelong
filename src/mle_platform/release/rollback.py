"""Registry alias movement and active-manifest activation with compensation."""

from __future__ import annotations

from mle_platform.contracts.synthaml import ModelReleaseManifest
from mle_platform.registry.interface import ModelRegistryPort

from .release_manifest import AtomicReleaseManifestRepository


class ReleaseController:
    """Coordinate two control planes without pretending they share a transaction.

    Registry alias movement and file-system pointer publication cannot be truly
    atomic. If pointer publication fails after an alias move, the controller
    restores the prior alias when an active release exists. Serving remains
    manifest-driven, so an uncommitted alias never silently becomes active.
    """

    def __init__(
        self,
        *,
        registry: ModelRegistryPort,
        manifests: AtomicReleaseManifestRepository,
        champion_alias: str = "champion",
    ) -> None:
        self.registry = registry
        self.manifests = manifests
        self.champion_alias = champion_alias

    def _previous_active(self) -> ModelReleaseManifest | None:
        try:
            return self.manifests.load_active()
        except FileNotFoundError:
            return None

    def activate(self, manifest: ModelReleaseManifest) -> ModelReleaseManifest:
        previous = self._previous_active()
        self.registry.set_alias(
            model_name=manifest.registered_model_name,
            alias=self.champion_alias,
            model_version=manifest.model_version,
        )
        try:
            self.manifests.publish(manifest)
        except Exception as publish_error:
            if (
                previous is not None
                and previous.registered_model_name == manifest.registered_model_name
            ):
                try:
                    self.registry.set_alias(
                        model_name=previous.registered_model_name,
                        alias=self.champion_alias,
                        model_version=previous.model_version,
                    )
                except Exception as compensation_error:
                    raise RuntimeError(
                        "release pointer publication failed and champion alias "
                        "compensation also failed; manual reconciliation is required"
                    ) from compensation_error
            raise publish_error
        return manifest

    def rollback(self, *, release_id: str) -> ModelReleaseManifest:
        prior = self.manifests.load_release(release_id)
        return self.activate(prior)
