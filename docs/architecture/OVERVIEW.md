# Architecture Overview

## Purpose

This repository hosts machine-learning workloads whose feature production is owned elsewhere. The reference workload is SynthAML fraud detection, supplied by the sibling `temporal-mle-data-contract` repository.

The design separates five kinds of authority:

1. **feature authority** — entity grain, event time, rolling and periodic feature mathematics;
2. **training authority** — model-facing table, matured labels, run and dataset identity;
3. **release authority** — promotion decision, immutable release manifest, active pointer;
4. **serving authority** — exact feature vector, model artifact, threshold, response and trace;
5. **monitoring authority** — drift/performance evidence and the policy that interprets it.

## Capability layers

```text
projects/synthaml
    workload-specific mapping and application services
            ↓
contracts + platform policies
    release, retrieval, decision, trace, monitoring
            ↓
external adapters
    Feast, MLflow, BentoML, Evidently
            ↓
orchestration and infrastructure
    Dagster, FastAPI, Compose, PostgreSQL, Redis, MinIO
```

Project code may depend on platform contracts. External adapters implement platform capabilities. Orchestration calls project/platform functions; it does not own domain semantics.

## Control plane and data plane

### Control plane

- validate the cross-repository contract;
- construct the matured-label training population;
- register and evaluate a candidate;
- publish an immutable release manifest;
- move the active-release pointer;
- compensate or roll back when activation fails;
- produce monitoring observations.

### Data plane

- accept an entity and evaluation timestamp;
- resolve one active release;
- retrieve exactly the required online feature vector;
- load the referenced model artifact;
- produce a probability and threshold decision;
- append a prediction trace;
- fail closed when any required boundary is invalid.

## One release identity

A release manifest binds:

- release ID;
- model name and registry version;
- run ID and model URI;
- feature-schema version and ordered feature list;
- training-dataset identity;
- metrics and decision threshold;
- code revision and creation time.

Serving resolves this manifest rather than asking a registry for `latest`.

## Replaceable seams

The core depends on capability interfaces, not SDK objects:

- `FeatureStorePort` → Feast today;
- `ModelRegistryPort` → MLflow today;
- model runtime → BentoML today;
- monitoring adapter → Evidently today;
- release repository → local immutable JSON today;
- prediction trace → JSONL today.

The local implementations prove behavior and failure semantics. A production deployment can replace them without changing the release and serving contracts.

## Evidence architecture

The evidence ladder intentionally separates:

```text
core state machine
→ real sibling-repository handoff
→ one SDK boundary per process
→ live service
→ composed infrastructure
```

This keeps environment and SDK failures distinguishable from architectural failures and allows the minimum integration to run on a constrained development machine.
