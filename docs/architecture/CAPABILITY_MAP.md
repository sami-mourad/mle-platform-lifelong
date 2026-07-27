# Platform Capability Map

Technologies are current adapters, not the architecture itself.

| Capability | Platform authority | Current local implementation | Production replacement path |
|---|---|---|---|
| Feature contract | versioned JSON + typed model | `SynthAMLFeatureContract` | schema registry / governed contract service |
| Snapshot validation | project adapter | pandas/PyArrow checks | distributed validation job |
| Historical/online features | `FeatureStorePort` | Feast | managed feature store or custom store |
| Training population | matured-label and temporal rules | SynthAML training adapter | warehouse/compute job |
| Registry | `ModelRegistryPort` | MLflow | managed registry or internal service |
| Promotion | `PromotionPolicy` | metric requirements and incumbent comparison | approval service / policy engine |
| Release identity | `ModelReleaseManifest` | immutable JSON history + active file | transactional metadata service / versioned object store |
| Model runtime | release-compatible probability interface | BentoML | Triton, managed endpoint, custom runtime |
| Serving API | typed request/response | FastAPI | gateway + horizontally scaled service |
| Decision policy | release threshold | `ReleaseDecisionPolicy` | configurable policy service |
| Prediction trace | append-only event contract | JSONL | Kafka, warehouse, ClickHouse, PostgreSQL |
| Delayed labels | independent label availability | Repository 1 adapter | durable supervision/event tables |
| Monitoring evidence | adapter result | Evidently | custom metrics pipeline / managed monitor |
| Monitoring decision | `MonitoringPolicy` | deterministic bounded states | incident/alert policy service |
| Orchestration | framework-light functions | Dagster reference assets | Airflow, Argo, managed orchestration |
| Infrastructure | explicit service topology | Docker Compose + Terraform foundation | environment-specific deployment modules |

## Extraction rule

A reusable capability must answer:

1. Which invariant does it own?
2. Which concrete callers need it?
3. Which implementation could replace the current one?
4. Which failure is isolated by the boundary?
5. Which contract test makes replacement safe?

Do not add an interface merely to make the tree look platform-like.
