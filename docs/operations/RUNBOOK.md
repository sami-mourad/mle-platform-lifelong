# Local Operations Runbook

## Evidence first

Before starting services, establish which evidence level is being exercised:

```bash
make synthaml-core
make synthaml-bridge REPO1=... SYNTHAML_SNAPSHOT=...
make synthaml-sdk REPO1=...
```

Do not use a Compose service being “up” as a substitute for a passing contract or adapter gate.

## Service map

| Service | Default port | Role |
|---|---:|---|
| SynthAML API | 8000 | typed score and health endpoints |
| MLflow | 5000 | run, artifact, and registry metadata |
| Dagster webserver | 3000 | orchestration UI |
| PostgreSQL | 5432 | MLflow and Dagster metadata |
| MinIO | 9000/9001 | local object storage |
| Redis | 6379 | online/cache extension point |
| Prometheus | 9090 | telemetry collection |
| Grafana | 3001 | dashboards |

## API readiness failure

1. Call `/health/live` and `/health/ready` separately.
2. Confirm an active release manifest exists and validates.
3. Verify the release feature-schema version matches the configured feature contract.
4. Verify the referenced Bento artifact is locally available.
5. Verify the Feast repository applies and the expected feature service exists.
6. Keep the service in explicit degraded/manual-review mode until all release boundaries are valid.

## Incomplete or ambiguous feature vector

Expected behavior: no probability is produced.

1. inspect the release’s ordered feature list;
2. inspect Feast response keys and entity value;
3. distinguish missing data from qualified-name ambiguity;
4. repair materialization or naming;
5. add a regression test before restoring readiness.

Never patch the request path by zero-filling a required feature.

## Model artifact failure

1. reproduce against the immutable release manifest;
2. verify model URI, model version, and expected input width;
3. quarantine the broken release;
4. roll back to a known immutable release;
5. add a runtime or activation regression test.

## Activation failure

If the MLflow alias moved but active-manifest publication failed, the release controller attempts compensation. Verify:

- the active manifest still points to the previous release;
- the registry alias was restored;
- no partial history file is treated as active;
- the failed activation is preserved in logs.

Retry only after the release-store failure is understood.

## Monitoring shows no data

1. verify prediction traces were appended;
2. verify label events use the correct identity;
3. inspect label-availability timestamps and cutoff;
4. confirm the matured population is nonempty;
5. confirm required metrics are present in the Evidently report.

Pending labels must remain pending; do not convert them to negative outcomes to force a metric.

## Compose recovery order

When exercising the broader local topology:

1. PostgreSQL and MinIO;
2. MLflow;
3. Dagster user code, webserver, and daemon;
4. Feast/feature materialization dependencies;
5. SynthAML API;
6. Prometheus and Grafana.

Compose is deployment evidence, not part of the minimum release gate.
