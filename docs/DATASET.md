# Dataset Provenance and Use

## Primary workload

The main demonstration uses SynthAML, a synthetic anti-money-laundering dataset, through the companion `temporal-mle-data-contract` repository.

This repository does not vendor the full dataset or the generated feature snapshot. The bridge receives a local Parquet path and validates it against the versioned feature contract.

Before redistributing source data, derived samples, trained artifacts, or benchmark claims, verify the authoritative licence and attribution requirements for the exact dataset files used.

## Public fixture policy

A public repository may include only a deliberately small, derived fixture when all of the following are true:

- redistribution is permitted;
- the fixture cannot be mistaken for a benchmark dataset;
- provenance and transformation are documented;
- no sensitive or identifying data are present;
- the fixture is needed for a deterministic test or example.

Otherwise, keep data outside Git and document how to obtain or generate it.

## Generic fallback project

The repository retains a small imbalanced-classification project as a platform smoke test. It can fetch OpenML dataset 310 (`mammography`) or use an explicitly marked deterministic synthetic disaster-recovery fixture.

The OpenML dataset is not redistributed here. A maintainer must verify authoritative terms before publishing derived data, trained models, or commercial benchmark claims from it.

## Interpretation

Both workloads are platform demonstrations. They are not medical, financial, compliance, or investigative decision systems and must not be presented as production risk models.
