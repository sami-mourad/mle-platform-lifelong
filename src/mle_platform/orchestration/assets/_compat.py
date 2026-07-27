"""Optional Dagster decorators so pure functions remain directly testable."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

try:
    from dagster import asset as _asset
except ImportError:  # local unit tests do not require Dagster
    _asset = None


def asset_compat(*args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    if _asset is not None:
        return _asset(*args, **kwargs)

    def decorate(function: Callable[..., Any]) -> Callable[..., Any]:
        return function

    return decorate
