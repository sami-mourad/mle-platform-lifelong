# Contributing

This is a portfolio reference implementation, but changes should follow the same evidence standard as a maintained platform repository.

1. Start from a failing test, an explicit invariant, or an accepted ADR.
2. Keep workload-specific assumptions under `src/mle_platform/projects/`.
3. Keep orchestration as a caller of reusable computation, not its owner.
4. Keep external SDK behavior behind adapter boundaries.
5. Add failure-path coverage for schema drift, incomplete vectors, partial writes, fallback, compensation, and rollback.
6. Update the runbook or validation document when operational behavior changes.
7. Do not add infrastructure solely because it appears in common MLOps diagrams.

Before opening a change:

```bash
make lint
make type
make test
make audit
```

Changes to public contracts require a versioned schema and a migration note.
