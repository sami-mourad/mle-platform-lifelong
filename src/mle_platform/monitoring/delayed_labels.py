"""Delayed-label population construction delegated to Repository 1 semantics."""

from __future__ import annotations

from typing import Any, Protocol, cast


class _DelayedSupervisionBuilder(Protocol):
    @classmethod
    def prepare_population(cls, **kwargs: Any) -> Any:
        """Build the label-mature monitoring population."""

    @classmethod
    def summary(cls, population: Any) -> dict[str, Any]:
        """Summarize label maturity and observed performance."""

    @classmethod
    def run_reports(cls, **kwargs: Any) -> dict[str, Any]:
        """Run monitoring reports and return their artifact paths."""


class DelayedLabelPopulationBuilder:
    """Stable platform façade over Repository 1 delayed-supervision semantics.

    The import is intentionally lazy so release, serving, and contract tests can
    run without importing the feature repository. Monitoring still fails clearly
    when Repository 1 is not installed.
    """

    @staticmethod
    def _delegate() -> type[_DelayedSupervisionBuilder]:
        try:
            from temporal_mle.platform_integration import (
                DelayedSupervisionMonitoringBuilder,
            )
        except ImportError as error:
            raise RuntimeError(
                "Repository 1 (temporal-mle) is required for delayed-label "
                "monitoring; install it with `python -m pip install -e "
                "../temporal-mle-data-contract`."
            ) from error
        return cast(
            type[_DelayedSupervisionBuilder],
            DelayedSupervisionMonitoringBuilder,
        )

    @classmethod
    def prepare_population(cls, **kwargs: Any) -> Any:
        return cls._delegate().prepare_population(**kwargs)

    @classmethod
    def summary(cls, population: Any) -> dict[str, Any]:
        return cls._delegate().summary(population)

    @classmethod
    def run_reports(cls, **kwargs: Any) -> dict[str, Any]:
        return cls._delegate().run_reports(**kwargs)
