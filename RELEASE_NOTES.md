# v0.1.0 — SynthAML Minimum Integration Release

This release establishes the first public, bounded integration of the temporal feature repository with the MLE hosting platform.

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
