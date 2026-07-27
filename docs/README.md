# Documentation Map

This page identifies the authoritative public documents. Historical overlay manifests, raw review worksheets, generated file maps, binary audits, and superseded runbooks are intentionally excluded from the public release.

## Start here

| Question | Authoritative document |
|---|---|
| What does the platform do? | [`../README.md`](../README.md) |
| How is it structured? | [`architecture/OVERVIEW.md`](architecture/OVERVIEW.md) |
| How do the two repositories integrate? | [`architecture/SYNTHAML_INTEGRATION.md`](architecture/SYNTHAML_INTEGRATION.md) |
| How does release activation work? | [`architecture/RELEASE_LIFECYCLE.md`](architecture/RELEASE_LIFECYCLE.md) |
| How do I run the complete demo? | [`guides/SYNTHAML_DEMO.md`](guides/SYNTHAML_DEMO.md) |
| What has actually been validated? | [`../VALIDATION.md`](../VALIDATION.md) |
| What is intentionally unfinished? | [`ROADMAP.md`](ROADMAP.md) |

## Architecture

- [`architecture/OVERVIEW.md`](architecture/OVERVIEW.md) — layers, control plane, data plane, and extension points.
- [`architecture/BOUNDARIES.md`](architecture/BOUNDARIES.md) — payload and authority boundaries.
- [`architecture/CAPABILITY_MAP.md`](architecture/CAPABILITY_MAP.md) — reusable capabilities versus current adapters.
- [`architecture/FAILURE_MODES.md`](architecture/FAILURE_MODES.md) — expected behavior and recovery.
- [`architecture/RELEASE_LIFECYCLE.md`](architecture/RELEASE_LIFECYCLE.md) — promotion, activation, compensation, and rollback.
- [`architecture/ADRs/`](architecture/ADRs/) — accepted architectural decisions.

## Operations and evidence

- [`operations/RUNBOOK.md`](operations/RUNBOOK.md) — local service and recovery procedures.
- [`DATASET.md`](DATASET.md) — dataset provenance and redistribution boundaries.
- [`../evidence/README.md`](../evidence/README.md) — release-evidence policy.
- [`reviews/PLATFORM_READINESS.md`](reviews/PLATFORM_READINESS.md) — high-leverage findings from the consolidation review.

## Engineering principles

- [`engineering/REVIEW_PRINCIPLES.md`](engineering/REVIEW_PRINCIPLES.md) — the repository-review method used to distinguish scaffolding from capability.

Documents under this tree describe the current repository. Working notes and obsolete merge instructions should stay outside version control rather than becoming competing authorities.
