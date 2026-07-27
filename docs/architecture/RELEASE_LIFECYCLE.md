# SynthAML Release Lifecycle

## Candidate

The training service validates the feature snapshot, excludes labels that are not available by the maturity cutoff, trains through the registry adapter, and returns a complete release candidate identity.

## Promotion

`PromotionPolicy` evaluates required metrics using explicit higher-is-better or lower-is-better direction. A candidate is rejected when:

- a required metric is missing or nonfinite;
- an absolute threshold is not met; or
- regression against the incumbent exceeds the configured allowance.

No alias or active pointer moves before promotion succeeds.

## Activation

The release controller coordinates two independent control planes:

1. the model-registry alias;
2. the immutable release repository and active pointer.

Activation order:

```text
remember prior active release
→ move registry alias to approved model version
→ publish immutable release history
→ atomically replace active-release pointer
```

This is not described as one cross-system transaction. If manifest publication fails after the alias moves, the controller attempts to restore the prior alias. Serving remains manifest-driven, so an alias movement alone cannot deploy a model.

## Serving

The serving application loads the active manifest and uses the manifest’s:

- ordered feature list;
- feature-schema version;
- model artifact identity;
- decision threshold;
- release ID.

The prediction trace records the same identity, allowing later monitoring to reconstruct which release made the decision.

## Rollback

Rollback selects an existing immutable release, moves the registry alias to its model version, and republishes that release as active. Rollback creates no new model and does not resolve `latest`.

## Future production store

The local file repository proves immutability, manifest-last publication, compensation, and rollback behavior. A multi-writer deployment should replace it with a transactional metadata service or a versioned object store with compare-and-swap semantics.
