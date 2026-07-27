# SynthAML Minimum Integration Runbook

This runbook proves the system in bounded layers. Run each heavy SDK boundary in a fresh process; do not start the full Compose topology merely to prove the platform core.

## 0. Directory layout

```text
workspace/
├── temporal-mle-data-contract/
└── mle-platform-lifelong/
```

Repository 1 should already have produced:

```text
data/demo/end_to_end_8/13_final_feature_snapshot_table.parquet
```

Confirm it:

```bash
test -f ../temporal-mle-data-contract/data/demo/end_to_end_8/13_final_feature_snapshot_table.parquet
```

## 1. Create the environment

```bash
cd ../mle-platform-lifelong
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

## 2. L0–L1: platform core

```bash
make synthaml-core
```

Expected gates:

```text
00_environment_core
01_compile
02_overlay_verify
03_repository_audit
04_core_tests
05_hosting_thin_slice
```

The thin slice proves release publication, exact vector ordering, scoring, decision policy, trace persistence, and manual-review behavior without requiring the external SDKs.

## 3. L2: real Repository 1 bridge

```bash
python -m pip install -e '.[synthaml-core]'
python -m pip install -e ../temporal-mle-data-contract

make synthaml-bridge \
  REPO1=../temporal-mle-data-contract \
  SYNTHAML_SNAPSHOT=../temporal-mle-data-contract/data/demo/end_to_end_8/13_final_feature_snapshot_table.parquet
```

The bridge checks:

- compatible package and schema identities;
- one row per feature grain;
- required entity and timestamp columns;
- exact model-facing feature availability;
- finite numeric values.

## 4. Inspect supervision columns

Before training from the real snapshot:

```bash
python - <<'PY'
import pandas as pd

path = "../temporal-mle-data-contract/data/demo/end_to_end_8/13_final_feature_snapshot_table.parquet"
frame = pd.read_parquet(path)
print(frame.shape)
print(frame.columns.tolist())
for name in ["final_outcome", "label_available_timestamp"]:
    if name in frame:
        print(name, frame[name].value_counts(dropna=False).head())
PY
```

Change target/label arguments only when the actual contract requires it. Do not encode pending labels as negatives.

## 5. L3: external SDK boundaries

```bash
python -m pip install -e '.[synthaml-sdk]'

make synthaml-sdk \
  REPO1=../temporal-mle-data-contract
```

Expected gates:

```text
20_environment_sdk
21_feast_boundary
22_mlflow_boundary
23_bentoml_boundary
24_evidently_boundary
25_sdk_release_demo
```

Each boundary runs in an isolated subprocess. A missing SDK is a failure for this profile.

## 6. Complete minimum release

```bash
make synthaml-all \
  REPO1=../temporal-mle-data-contract \
  SYNTHAML_SNAPSHOT=../temporal-mle-data-contract/data/demo/end_to_end_8/13_final_feature_snapshot_table.parquet
```

The run stops at the first failed boundary and writes one log per gate plus `synthaml_all_gate_summary.json`.

## 7. Publish sanitized evidence

```bash
make release-evidence \
  REPO1=../temporal-mle-data-contract \
  SYNTHAML_SNAPSHOT=../temporal-mle-data-contract/data/demo/end_to_end_8/13_final_feature_snapshot_table.parquet
```

Inspect:

```bash
python -m json.tool evidence/releases/v0.1.0/synthaml_all_gate_summary.json
```

Commit the summary JSON only. Raw logs and generated release artifacts are ignored.

## 8. Train/register/activate from the real snapshot

```bash
PYTHONPATH=src:. python examples/synthaml_platform_overlay_demo.py \
  --feature-snapshot ../temporal-mle-data-contract/data/demo/end_to_end_8/13_final_feature_snapshot_table.parquet \
  --target-column final_outcome \
  --positive-label Reported \
  --negative-label Dismissed \
  --label-available-timestamp-column label_available_timestamp \
  --maturity-cutoff 2021-12-31T23:59:59Z \
  --decision-threshold 0.50 \
  --output-directory .artifacts/synthaml/mlflow-release
```

This is a stronger L3/L4 bridge only when the real snapshot contains enough mature examples for the configured training split.

## 9. Local API

Configure the feature contract, Feast repository, release directory, and trace path:

```bash
export SYNTHAML_FEATURE_CONTRACT_PATH=contracts/synthaml/feature_contract_v3_1_1.json
export SYNTHAML_FEAST_REPO=../temporal-mle-data-contract/feature_repo
export SYNTHAML_RELEASE_DIR=.artifacts/synthaml/mlflow-release/releases
export SYNTHAML_PREDICTION_LOG=.artifacts/synthaml/predictions.jsonl

python -m mle_platform.projects.synthaml.service
```

In a second shell:

```bash
curl -fsS http://localhost:8000/health/live
curl -fsS http://localhost:8000/health/ready
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
curl -fsS -X POST http://localhost:8000/predict \
  -H 'content-type: application/json' \
  -d "{\"entity_id\":\"930\",\"evaluation_timestamp\":\"$NOW\"}"
```

A score is returned only when release identity, feature vector, model artifact, and request time are valid.

## 10. Optional infrastructure

```bash
make compose-core
make dagster-materialize
make compose-observability
```

These commands demonstrate the broader topology. They are not required for the v0.1.0 minimum integration release.

## Stopping rule

For portfolio publication, stop when:

- L0–L3 pass;
- the sanitized all-gate summary is tied to the Git commit;
- the README and release notes link the compatible Repository 1 version;
- CI passes from a clean checkout.

Do not delay publication for distributed deployment, Kubernetes, or large-scale load evidence.
