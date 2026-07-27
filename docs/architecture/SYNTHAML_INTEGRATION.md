# SynthAML Integration

## Repository ownership

### `temporal-mle-data-contract`

Owns:

- SynthAML normalization and entity/event-time semantics;
- temporal anchors and point-in-time histories;
- rolling and periodically weighted feature computation;
- approved feature snapshot schema and output;
- Feast feature definitions and offline/online parity utilities;
- independent label events and label availability.

### `mle-platform-lifelong`

Owns:

- cross-repository compatibility validation;
- model-facing training population;
- registry and promotion lifecycle;
- immutable release identity and rollback;
- online serving and decision policy;
- prediction traces;
- monitoring evidence and operational policy;
- orchestration and deployment extension points.

## Training journey

```text
Repository 1 approved snapshot
→ bridge validation
→ matured-label filtering
→ historical/model-facing feature table
→ MLflow training and registration
→ metric-based promotion
→ immutable release activation
```

## Serving journey

```text
entity + evaluation timestamp
→ active release
→ exact Feast online vector
→ BentoML probability
→ release threshold
→ decision + release identity
→ append-only prediction trace
```

## Monitoring journey

```text
prediction trace
+ independent label events
→ matured prediction/label population
→ Evidently drift/performance report
→ platform monitoring policy
→ healthy / investigate / no_data
```

## Dependency direction

Repository 2 installs Repository 1 only at genuine integration seams. The release, serving, and monitoring core can be imported and tested without Repository 1 or the heavy SDKs installed.

The two repositories must not copy each other’s source modules. Compatibility is established through package version, JSON schemas, and executable bridge tests.
