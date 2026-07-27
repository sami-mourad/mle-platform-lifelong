# Release Evidence

This directory contains small, sanitized summaries tied to immutable releases.

The gate runner writes raw logs, generated releases, prediction traces, and SDK artifacts alongside the summary. `.gitignore` excludes those outputs because they may contain machine-specific paths or generated binaries.

Generate the v0.1.0 evidence set with:

```bash
make release-evidence \
  REPO1=../temporal-mle-data-contract \
  SYNTHAML_SNAPSHOT=../temporal-mle-data-contract/data/demo/end_to_end_8/13_final_feature_snapshot_table.parquet
```

Review the generated summary before committing it:

```bash
python -m json.tool \
  evidence/releases/v0.1.0/synthaml_all_gate_summary.json
```

Only the summary JSON is intended for version control. CI logs remain available through GitHub Actions.
