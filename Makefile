SHELL := /usr/bin/env bash

PYTHON ?= python
PIP ?= $(PYTHON) -m pip
VENV ?= .venv
REPO1 ?= ../temporal-mle-data-contract
SYNTHAML_SNAPSHOT ?= $(REPO1)/data/demo/end_to_end_8/13_final_feature_snapshot_table.parquet
SYNTHAML_OUTPUT ?= .artifacts/synthaml
RELEASE_VERSION ?= v0.1.0
RELEASE_EVIDENCE ?= evidence/releases/$(RELEASE_VERSION)

.PHONY: help venv doctor install install-synthaml-core install-synthaml-sdk lint format type test unit integration train-local serve-local smoke smoke-fallback synthaml-core synthaml-bridge synthaml-sdk synthaml-all release-evidence synthaml-thin-demo synthaml-mlflow-demo serve-synthaml compose-core compose-observability compose-down dagster-materialize audit clean

help:
	@printf '%s\n' \
	  'make venv                    Create .venv with the selected Python interpreter' \
	  'make install                 Install core development dependencies in the active environment' \
	  'make install-synthaml-core   Add Parquet support and editable Repository 1' \
	  'make install-synthaml-sdk    Add Feast/MLflow/BentoML/Evidently adapters' \
	  'make test                    Run the complete local pytest inventory' \
	  'make synthaml-core           Run dependency-light hosting gates' \
	  'make synthaml-bridge         Validate Repository 1 schemas and final snapshot' \
	  'make synthaml-sdk            Run SDK boundaries in isolated processes' \
	  'make synthaml-all            Run core, bridge, and SDK evidence levels' \
	  'make release-evidence        Run all gates into evidence/releases/<version>' \
	  'make synthaml-thin-demo      Run the no-SDK hosting proof' \
	  'make synthaml-mlflow-demo    Train/register from the Repository 1 snapshot' \
	  'make serve-synthaml          Start the Feast/Bento-backed API' \
	  'make compose-core            Start the broader local platform topology' \
	  'make audit                   Audit repository shape and collision rules'

venv:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip

install:
	$(PIP) install --upgrade pip
	$(PIP) install -e '.[dev]'

install-synthaml-core: install
	$(PIP) install -e '.[synthaml-core]'
	$(PIP) install -e '$(REPO1)'

install-synthaml-sdk: install-synthaml-core
	$(PIP) install -e '.[synthaml-sdk]'

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

format:
	$(PYTHON) -m ruff check . --fix
	$(PYTHON) -m ruff format .

type:
	$(PYTHON) -m mypy src tools

unit:
	$(PYTHON) -m pytest tests/unit tests/contract

integration:
	$(PYTHON) -m pytest -m integration

test:
	$(PYTHON) -m pytest -ra

train-local:
	MLFLOW_REGISTER_MODELS=false MLFLOW_TRACKING_URI= $(PYTHON) -m mle_platform.projects.dummy_imbalance.train

serve-local:
	$(PYTHON) -m mle_platform.projects.dummy_imbalance.service

smoke:
	$(PYTHON) scripts/smoke_api.py --base-url http://localhost:8000

smoke-fallback:
	$(PYTHON) scripts/smoke_api.py --base-url http://localhost:8000 --force-fallback

synthaml-core:
	$(PYTHON) tools/run_synthaml_gates.py --profile core --output-directory $(SYNTHAML_OUTPUT)/evidence

synthaml-bridge:
	$(PYTHON) tools/run_synthaml_gates.py --profile bridge --repository-1 $(REPO1) --feature-snapshot $(SYNTHAML_SNAPSHOT) --output-directory $(SYNTHAML_OUTPUT)/evidence

synthaml-sdk:
	$(PYTHON) tools/run_synthaml_gates.py --profile sdk --repository-1 $(REPO1) --output-directory $(SYNTHAML_OUTPUT)/evidence

synthaml-all:
	$(PYTHON) tools/run_synthaml_gates.py --profile all --repository-1 $(REPO1) --feature-snapshot $(SYNTHAML_SNAPSHOT) --output-directory $(SYNTHAML_OUTPUT)/evidence

release-evidence:
	$(PYTHON) tools/run_synthaml_gates.py --profile all --repository-1 $(REPO1) --feature-snapshot $(SYNTHAML_SNAPSHOT) --output-directory $(RELEASE_EVIDENCE)

synthaml-thin-demo:
	PYTHONPATH=src $(PYTHON) examples/synthaml_hosting_thin_slice.py --output-directory $(SYNTHAML_OUTPUT)/thin-slice

synthaml-mlflow-demo:
	PYTHONPATH=src $(PYTHON) examples/synthaml_platform_overlay_demo.py \
	  --feature-snapshot $(SYNTHAML_SNAPSHOT) \
	  --target-column final_outcome \
	  --positive-label Reported \
	  --negative-label Dismissed \
	  --label-available-timestamp-column label_available_timestamp \
	  --maturity-cutoff 2021-12-31T23:59:59Z \
	  --output-directory $(SYNTHAML_OUTPUT)/mlflow-release

serve-synthaml:
	$(PYTHON) -m mle_platform.projects.synthaml.service

compose-core:
	docker compose up -d --build postgres minio minio-init redis mlflow dagster-user-code dagster-webserver dagster-daemon api

compose-observability:
	docker compose --profile observability up -d prometheus grafana

compose-down:
	docker compose --profile observability down -v

dagster-materialize:
	docker compose exec dagster-user-code dagster job execute -m mle_platform.orchestration.definitions -j full_retrain_job

audit:
	PYTHONPATH=src $(PYTHON) tools/repo_audit.py . --format markdown

clean:
	rm -rf .data .artifacts .mlruns mlruns .dagster .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage build dist
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type d -name '*.egg-info' -prune -exec rm -rf {} +
