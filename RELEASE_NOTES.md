# v0.1.1 — Green CI and Optional Dagster Boundary

Patch release of the bounded SynthAML minimum integration.

This release preserves the v0.1.0 feature and lifecycle contracts while:

- satisfying the public Ruff, formatting, mypy, and pytest gates;
- making optional Dagster Definitions loading safe when Dagster is absent or
  exposes an incompatible API; and
- aligning the README validation status with the green main branch.

No feature-schema, model-release-contract, or serving-policy change.

## Validated path

- dependency-light platform lifecycle;
- real Repository 1 schema and snapshot bridge;
- Feast feature-store boundary;
- MLflow training and registry boundary;
- BentoML artifact/runtime boundary;
- Evidently monitoring boundary;
- immutable release activation;
- fail-closed feature retrieval;
- prediction-trace persistence; and
- synthetic SDK release journey.

## Architecture

Repository 1 owns point-in-time feature correctness. Repository 2 owns model promotion, release identity, serving, traceability, and monitoring policy. The boundary is versioned and executable.

## Explicit non-claims

This release does not claim multi-node production deployment, high availability, production IAM, high-concurrency online storage, production-scale throughput, or load-tested HTTP service.
