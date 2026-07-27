# MLE Repository Review Principles

## 1. Begin with ownership, not file count

For every module ask what invariant it owns, what state it mutates, who calls it, what could replace it, and what is the smallest reason it must change.

A folder is not an architecture boundary unless dependency direction enforces it.

## 2. Trace three journeys

### Data journey

Source → validation → transformation → persisted representation → training/serving use.

### Model journey

Code/config/data → run → evaluation → version → promotion → deployment → rollback.

### Request journey

Input contract → feature retrieval → model call → policy → response → telemetry.

If any journey requires hidden global state, notebook state, or manual file copying, mark it.

## 3. Prefer semantic names over implementation names

Good: `promotion_policy.py`, `prediction_contract.py`, `deployment_manifest.py`.

Weak: `utils.py`, `helpers.py`, `common.py`, `processor.py`, `manager.py`.

## 4. Inspect import direction

Healthy:

```text
project adapter → platform interface → external tool adapter
```

Domain computation should be runnable without Dagster, MLflow, Docker, or cloud credentials.

## 5. Locate side effects

Network calls, database writes, filesystem writes, environment reads, registration, subprocesses, and global caches should occur at explicit boundaries.

## 6. Read tests as claims

Look for claims about leakage, schema compatibility, determinism, idempotency, partial writes, fallback, rollback, retries, version resolution, serving contracts, and monitoring semantics.

## 7. Review configuration as an API

Demand documented precedence, typed values, environment separation, secret references, startup validation, safe defaults, and no machine-specific paths.

## 8. Review DataFrames as schemas, not bags of columns

Identify entity/event keys, correctness timestamp, nullability, units/ranges, model inputs, labels, metadata, and contract version.

## 9. Distinguish scaffolding from capability

A capability requires:

```text
implementation + configuration + test + run path + failure behavior + documentation
```

## 10. Measure change radius

Count files that change when adding a model/project, changing storage/orchestrator, adding an API field, changing promotion, or rolling back.

## 11. Look for independently replaceable seams

Useful seams include artifact store, registry, feature retrieval, runtime, launcher, telemetry, and decision policy. Do not add interfaces without a real second implementation or failure-isolation need.

## 12. Read deletion paths

Good architecture lets you remove MLflow without breaking local training, Dagster without breaking model code, Redis without breaking unrelated serving, and one project without altering platform core.

## 13. Look for operational truth

Check processes, persistence, logs, backups, health semantics, secret delivery, slowness behavior, alerts, and artifact authority.

## 14. Demand evidence for “production-ready”

Without clean-checkout runs, capacity numbers, failure drills, recovery, security assumptions, retention, upgrade strategy, and ownership, call it production-minded—not production-ready.
