# Contract-First MLE Platform for SynthAML

[![CI](https://github.com/sami-mourad/mle-platform-lifelong/actions/workflows/ci.yml/badge.svg)](https://github.com/sami-mourad/mle-platform-lifelong/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12–3.13](https://img.shields.io/badge/Python-3.12%E2%80%933.13-blue.svg)](pyproject.toml)

A production-oriented local reference architecture for turning a point-in-time temporal feature snapshot into a controlled model release, online decision, prediction trace, and delayed-label monitoring observation.

This repository is the **model-lifecycle and hosting authority** for the companion [`temporal-mle-data-contract`](https://github.com/sami-mourad/temporal-mle-data-contract) project.

## v0.1.1 validation status

The minimum integration sequence passes across all defined gates.
Public source-quality and lifecycle checks run through GitHub Actions,
and the committed release summary records the bounded integration evidence.

| Boundary | Status |
|---|---|
| Dependency-light lifecycle core | Passed |
| Real Repository 1 snapshot contract | Passed |
| Feast integration | Passed |
| MLflow registration and training | Passed |
| BentoML model artifact/runtime | Passed |
| Evidently monitoring | Passed |
| Synthetic release journey | Passed |
| Full distributed production deployment | Not claimed |

The public authorities after publication are the GitHub Actions run and a regenerated release summary produced with `make release-evidence`. Raw local logs remain untracked because they may contain machine-specific paths.

## System boundary

```text
Repository 1: temporal-mle-data-contract

> **Naming note:** the Git checkout is `temporal-mle-data-contract`, the installed
> distribution is `temporal-mle`, and the Python import is `temporal_mle`.
> `temporal_mle_data_contract` is not an importable package.

SynthAML transactions
  → entity/event-time contracts
  → rolling and periodically weighted features
  → point-in-time validation
  → approved Parquet feature snapshot
  → Feast definitions

                    versioned handoff
                           ↓

Repository 2: mle-platform-lifelong

cross-repository validation
  → matured-label training population
  → MLflow candidate registration
  → promotion policy
  → immutable release manifest
  → active-release pointer
  → Feast vector + BentoML runtime
  → score + threshold decision
  → append-only prediction trace
  → delayed-label and drift observation
```

Repository 1 owns feature mathematics, temporal anchors, and snapshot correctness. This repository owns model promotion, release identity, serving behavior, traceability, and monitoring policy. The repositories are joined through explicit contracts rather than copied implementation.

## Why this architecture

The portfolio claim is not “many MLOps tools are installed.” It is one bounded and inspectable lifecycle:

```text
feature contract
→ candidate model
→ promotion decision
→ immutable release
→ exact online vector
→ model probability
→ decision policy
→ prediction trace
→ monitoring evidence
```

The core lifecycle is dependency-light. Feast, MLflow, BentoML, Evidently, Dagster, and infrastructure services sit behind explicit integration boundaries, so an SDK or environment failure can be diagnosed without invalidating the platform state machine.

## Quick start

### 1. Core lifecycle proof

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'

make synthaml-core
```

This compiles the source, audits package boundaries, runs dependency-light tests, activates an immutable local release, retrieves a feature vector in contract order, records a prediction trace, and proves fail-closed behavior for an incomplete vector.

### 2. Real cross-repository bridge

Keep both repositories under one parent directory and install the feature repository:

```bash
python -m pip install -e '.[synthaml-core]'
python -m pip install -e ../temporal-mle-data-contract

make synthaml-bridge \
  REPO1=../temporal-mle-data-contract \
  SYNTHAML_SNAPSHOT=../temporal-mle-data-contract/data/demo/end_to_end_8/13_final_feature_snapshot_table.parquet
```

The bridge rejects package/schema drift, duplicate feature grain, the wrong schema version, and absent, null, or nonnumeric model inputs.

### 3. SDK boundaries

```bash
python -m pip install -e '.[synthaml-sdk]'

make synthaml-sdk \
  REPO1=../temporal-mle-data-contract
```

Feast, MLflow, BentoML, and Evidently run in isolated subprocesses. A requested SDK gate fails when its dependency is absent; it is not counted as a skipped success.

### 4. Complete minimum integration

```bash
make synthaml-all \
  REPO1=../temporal-mle-data-contract \
  SYNTHAML_SNAPSHOT=../temporal-mle-data-contract/data/demo/end_to_end_8/13_final_feature_snapshot_table.parquet
```

For a public release summary:

```bash
make release-evidence \
  REPO1=../temporal-mle-data-contract \
  SYNTHAML_SNAPSHOT=../temporal-mle-data-contract/data/demo/end_to_end_8/13_final_feature_snapshot_table.parquet
```

Commit the generated `synthaml_all_gate_summary.json`; keep raw `.txt` logs and generated model artifacts local.

## Architecture

| Layer | Responsibility | Primary paths |
|---|---|---|
| Contracts | feature, release, request, response, and trace schemas | `contracts/`, `src/mle_platform/contracts/` |
| Project adapter | SynthAML-specific training, serving, and monitoring | `src/mle_platform/projects/synthaml/` |
| Platform core | promotion, release, retrieval, runtime, decision, trace | `src/mle_platform/{release,serving,monitoring}/` |
| External adapters | Feast, MLflow, BentoML, Evidently | `src/mle_platform/{feature_store,registry,monitoring}/` |
| Orchestration | framework-light functions plus Dagster topology | `src/mle_platform/orchestration/` |
| Evidence plane | isolated gates, audits, examples, release summaries | `tools/`, `tests/`, `examples/`, `evidence/` |
| Infrastructure | local Compose and AWS foundation | `docker-compose*.yml`, `infra/` |

### Release authority

Serving resolves one immutable release manifest. A model-registry alias alone cannot deploy a model. Because the MLflow alias and active release pointer cannot share a transaction, activation uses compensation while the active manifest remains the serving authority.

### Fail-closed serving

Missing, ambiguous, or schema-incompatible features are not silently replaced with zeroes. The request returns an explicit degraded/manual-review outcome rather than an invalid probability.

### Monitoring authority

Evidently produces monitoring evidence. A separate platform policy converts drift, label maturity, and performance into bounded operational states such as `healthy`, `investigate`, or `no_data`.

## Dependency profiles

| Extra | Purpose |
|---|---|
| `dev` | tests, linting, typing, pre-commit |
| `synthaml-core` | Parquet snapshot bridge |
| `synthaml-sdk` | Feast, MLflow, BentoML, Evidently |
| `orchestration` | Dagster |
| `infra` | PostgreSQL, Redis, and object-store clients |
| `full-platform` | all optional runtime capabilities |

## Reviewer path

1. Read [`docs/architecture/OVERVIEW.md`](docs/architecture/OVERVIEW.md).
2. Inspect [`contracts/synthaml/feature_contract_v3_1_1.json`](contracts/synthaml/feature_contract_v3_1_1.json).
3. Run or read [`examples/synthaml_hosting_thin_slice.py`](examples/synthaml_hosting_thin_slice.py).
4. Review `release/`, `serving/`, and `monitoring/` before the external SDK adapters.
5. Follow the complete command sequence in [`docs/guides/SYNTHAML_DEMO.md`](docs/guides/SYNTHAML_DEMO.md).
6. Read [`VALIDATION.md`](VALIDATION.md) for claim boundaries and evidence policy.

The documentation authority map is in [`docs/README.md`](docs/README.md).

## Honest scope

This repository proves a bounded local architecture and minimum SDK integration. It does not claim multi-node production deployment, high availability, production IAM or secrets management, high-concurrency online storage, 16-million-row throughput, container recovery, or load-tested HTTP service. Those remain explicit roadmap and deployment gates.

## License

Source code and documentation are released under the [MIT License](LICENSE). Demonstration datasets and third-party dependencies retain their own terms; the full SynthAML dataset is not redistributed here.
