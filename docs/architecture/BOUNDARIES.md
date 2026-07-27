# Boundary and Contract Catalog

| Boundary | Producer | Consumer | Contract or authority | Required failure behavior |
|---|---|---|---|---|
| Feature snapshot | Repository 1 | SynthAML project adapter | feature schema version, entity grain, ordered model inputs | reject duplicates, absent/null/nonnumeric features, or version drift |
| Historical retrieval | Feast adapter | training service | `HistoricalFeatureRequest` | fail; never train on a partial feature table |
| Online retrieval | Feast adapter | serving application | `OnlineFeatureRequest` and release feature list | fail closed; never substitute zeroes |
| Candidate training | project training service | registry adapter | dataset identity, feature list, target and metrics | reject pending labels and invalid inputs |
| Registry result | MLflow adapter | release controller | model name, version, run ID, artifact URI | do not activate an incomplete identity |
| Promotion | metrics + incumbent | release controller | `PromotionPolicy` | reject missing metrics, threshold failure, or unacceptable regression |
| Release publication | release controller | serving application | immutable `ModelReleaseManifest` + active pointer | manifest remains serving authority; compensate alias on publication failure |
| Model execution | BentoML runtime | serving application | release model URI and ordered numeric vector | explicit degraded/manual-review response on load or inference failure |
| Prediction trace | serving application | monitoring | append-only `PredictionTraceContract` | scoring success is not returned until the trace append succeeds |
| Label event | source supervision | monitoring population builder | independent label time and availability | pending labels remain pending, never negative by default |
| Monitoring report | Evidently adapter | monitoring policy | drift count, row counts, matured-label metrics | absent required metrics produce `no_data`/investigate, not healthy |

## Review rule

Every new boundary must specify:

- payload and schema version;
- identity, entity key, and correctness timestamp;
- ordering requirements;
- retry and idempotency behavior;
- freshness expectation;
- retention and security policy;
- owning module;
- observable failure signal;
- contract test protecting replacement.
