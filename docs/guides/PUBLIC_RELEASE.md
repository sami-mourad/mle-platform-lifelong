# Initial Public Release Checklist

This repository was developed before Git tracking. The first public history should be honest, reviewable, and grouped by capability rather than fabricated as a long development chronology.

## 1. Final local checks

```bash
make lint
make type
make test
make audit
```

Run the cross-repository release evidence separately:

```bash
make release-evidence \
  REPO1=../temporal-mle-data-contract \
  SYNTHAML_SNAPSHOT=../temporal-mle-data-contract/data/demo/end_to_end_8/13_final_feature_snapshot_table.parquet
```

Inspect the generated summary and verify that it reports every planned gate as passed.

## 2. Initialize Git

```bash
git init -b main
git config user.name "Sami Mourad"
git config user.email "YOUR_GITHUB_EMAIL"
```

## 3. Commit in reviewable groups

### Commit 1 — platform core

```bash
git add \
  .gitignore .env.example pyproject.toml \
  LICENSE src contracts configs

git commit -m "feat: establish contract-first MLE platform core"
```

### Commit 2 — executable integration and infrastructure

```bash
git add \
  Makefile .pre-commit-config.yaml .github \
  tests examples tools scripts scorecards \
  docker-compose.yml docker-compose.synthaml.override.yml infra

git commit -m "test: add SynthAML integration gates and platform infrastructure"
```

### Commit 3 — public documentation

```bash
git add \
  README.md VALIDATION.md CONTRIBUTING.md SECURITY.md \
  CHANGELOG.md RELEASE_NOTES.md CITATION.cff docs

git commit -m "docs: publish architecture, validation, and release guidance"
```

### Commit 4 — sanitized release evidence

```bash
git add evidence/README.md
git add -f evidence/releases/v0.1.0/synthaml_all_gate_summary.json

git commit -m "chore: record v0.1.0 minimum integration evidence"
```

If the summary has not yet been regenerated after cleanup, commit only `evidence/README.md` and add the release summary in a later evidence commit.

## 4. Review the staged repository

```bash
git status --short
git ls-files | sort
git grep -nE '(api[_-]?key|secret|password|token)[[:space:]]*[:=]' -- . ':!*.lock'
git count-objects -vH
```

Verify that no dataset, feature snapshot, patch backup, build metadata, cache, model artifact, or raw local log is tracked.

## 5. Push privately first

```bash
gh auth login

gh repo create sami-mourad/mle-platform-lifelong \
  --private \
  --source=. \
  --remote=origin \
  --push \
  --description="Contract-first MLE platform for release, serving, traceability, and delayed-label monitoring."
```

Inspect the rendered README and Actions run, then change visibility to public.

## 6. Tag the release

```bash
git tag -a v0.1.0 -m "SynthAML minimum integration release"
git push origin v0.1.0

gh release create v0.1.0 \
  --title "v0.1.0 — SynthAML Minimum Integration Release" \
  --notes-file RELEASE_NOTES.md
```
