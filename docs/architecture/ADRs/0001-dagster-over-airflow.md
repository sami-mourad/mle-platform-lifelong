# ADR 0001: Use Dagster as the reference orchestrator

## Status

Accepted for this scaffold.

## Context

The platform is organized around durable data and model assets rather than only task sequences. The orchestration example should make asset lineage, checks, and materialization state visible.

## Decision

Use Dagster for the runnable reference implementation. Keep project functions framework-independent so an Airflow adapter can be added without rewriting training logic.

## Consequences

- asset graph and checks are first-class;
- Dagster metadata requires an operational database in the full profile;
- users familiar with Airflow must learn different primitives;
- orchestration cannot leak into model/business code.
