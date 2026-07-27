# Validation and Evidence

## Minimum integration status

Before the initial Git import, the maintainer completed the full bounded integration sequence in a Python 3.13 environment:

| Gate | Result |
|---|---|
| `00_environment_core` | Passed |
| `01_compile` | Passed |
| `02_overlay_verify` | Passed |
| `03_repository_audit` | Passed |
| `04_core_tests` | Passed |
| `05_hosting_thin_slice` | Passed |
| `10_environment_bridge` | Passed |
| `11_cross_repository_contract` | Passed |
| `20_environment_sdk` | Passed |
| `21_feast_boundary` | Passed |
| `22_mlflow_boundary` | Passed |
| `23_bentoml_boundary` | Passed |
| `24_evidently_boundary` | Passed |
| `25_sdk_release_demo` | Passed |

This establishes the **minimum local integration claim**: the real Repository 1 contract can cross into Repository 2, and the Feast, MLflow, BentoML, and Evidently adapters execute through their isolated boundaries.

## Public evidence authority

The initial local run predates Git. After cloning or cleaning the repository, regenerate evidence against the exact commit:

```bash
make release-evidence \
  REPO1=../temporal-mle-data-contract \
  SYNTHAML_SNAPSHOT=../temporal-mle-data-contract/data/demo/end_to_end_8/13_final_feature_snapshot_table.parquet
```

The command writes to `evidence/releases/v0.1.0/` by default.

Commit:

```text
evidence/releases/v0.1.0/synthaml_all_gate_summary.json
```

Do not commit:

- raw `.txt` logs containing local paths;
- generated BentoML/MLflow artifacts;
- feature snapshots or full datasets;
- local release manifests containing checkout-specific paths.

GitHub Actions is the authority for the dependency-light core on a clean checkout. The release summary is the authority for the sibling-repository and heavy-SDK gates.

## Evidence levels

| Level | Proof | Claim enabled |
|---|---|---|
| L0 | compile, source verification, repository audit | coherent package and contracts |
| L1 | dependency-light hosting thin slice | release and serving state machine |
| L2 | real Repository 1 snapshot bridge | executable cross-repository contract |
| L3 | isolated SDK integrations | locally hosted SynthAML integration |
| L4 | live HTTP score against a real active release | local service proof |
| L5 | Dagster/Compose and operational drills | deployment evidence |

The minimum release ends at L3. L4 and L5 are useful follow-on evidence but should not delay publication.

## Claim boundary

Passing L0–L3 does not prove cloud deployment, high availability, production IAM, load capacity, multi-writer durability, or disaster recovery. These are separate operational gates and are not implied by importing their supporting SDKs.
