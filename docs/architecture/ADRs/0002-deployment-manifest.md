# ADR 0002: Use immutable release manifests and an atomic active pointer

## Status

Accepted.

## Context

Resolving a mutable registry alias during online startup makes serving availability depend on the registry and does not fully identify the feature schema, dataset, threshold, or code revision. Publishing model files without a final pointer can also expose a partial release.

MLflow alias movement and release publication are separate control planes and cannot share one transaction.

## Decision

Publish each `ModelReleaseManifest` immutably in release history, then atomically replace a small active-release pointer. Serving resolves only the active manifest.

During activation, move the registry alias first and compensate it back to the previous model version if manifest publication fails. An alias movement alone is not a deployment.

## Consequences

- serving remains independent of live MLflow availability after release;
- release identity includes model, features, data, threshold, metrics, and code revision;
- rollback selects an immutable prior release;
- cross-control-plane activation is compensating, not globally atomic;
- the local file repository must be replaced before multi-writer production use.
