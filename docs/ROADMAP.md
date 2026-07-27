# Platform Roadmap

The repository should grow through proven reuse and measured operational requirements, not by collecting infrastructure.

## Stage 0 — Public reference vertical slice

Current release target:

- real Repository 1 snapshot bridge;
- isolated Feast, MLflow, BentoML, and Evidently boundaries;
- immutable releases, promotion, compensation, and rollback;
- fail-closed serving and prediction traces;
- clean-checkout CI and sanitized release evidence.

## Stage 1 — Complete local service proof

- activate a release trained from the real snapshot;
- score through the HTTP service;
- preserve one successful trace and one degraded/manual-review trace;
- measure p50/p95 latency and peak memory;
- execute one rollback or failed-activation recovery drill.

## Stage 2 — Second workload tests the abstractions

Add a genuinely different workload, such as recommendation or credit risk. Reuse the release and serving contracts without copying SynthAML assumptions. Extract a new platform abstraction only when both workloads need the same invariant.

## Stage 3 — Durable local adapters

Replace at least one demonstration implementation behind its existing contract:

- JSONL prediction trace → PostgreSQL or event stream;
- local release repository → transactional metadata store;
- local observation files → durable monitoring table.

Run the same contract tests against both implementations.

## Stage 4 — Deployment environments

Introduce environment modules, remote state, secret references, least-privilege IAM, image provenance, vulnerability scanning, resource limits, backup/restore, and staged release promotion.

## Stage 5 — Distributed/event-driven capabilities

Add only when measurements require them:

- Kafka/Pulsar for durable replay and fan-out;
- streaming compute for fresh stateful features;
- Ray/Kubernetes/Batch for distributed training;
- an analytical telemetry store when current persistence no longer meets query volume.

## Stopping rule

Do not delay applications for Stage 3–5. The portfolio release is credible when the minimum integration is reproducible, public, documented, and honest about its limits.
