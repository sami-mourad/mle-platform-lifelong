"""Fail-fast dependency doctor for each SynthAML evidence level."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import sys
from pathlib import Path

MODULES = {
    "core": ("fastapi", "numpy", "pandas", "pydantic", "sklearn"),
    "bridge": ("fastapi", "numpy", "pandas", "pydantic", "sklearn", "pyarrow", "temporal_mle"),
    "sdk": (
        "fastapi",
        "numpy",
        "pandas",
        "pydantic",
        "sklearn",
        "pyarrow",
        "temporal_mle",
        "polars",
        "feast",
        "mlflow",
        "bentoml",
        "evidently",
    ),
    "orchestration": ("dagster",),
}
PACKAGE_NAMES = {
    "sklearn": "scikit-learn",
    "temporal_mle": "temporal-mle",
}


def _version(module_name: str, module: object) -> str | None:
    package_name = PACKAGE_NAMES.get(module_name, module_name)
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return getattr(module, "__version__", None)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=[*MODULES, "all"], default="core")
    parser.add_argument("--repository-1", type=Path)
    args = parser.parse_args()
    names = sorted({name for profile in MODULES.values() for name in profile}) if args.profile == "all" else list(MODULES[args.profile])
    results: dict[str, dict[str, object]] = {}
    missing: list[str] = []
    for name in names:
        try:
            module = importlib.import_module(name)
        except Exception as error:  # dependency doctors should report the original exception
            results[name] = {"available": False, "error": f"{type(error).__name__}: {error}"}
            missing.append(name)
        else:
            results[name] = {"available": True, "version": _version(name, module)}

    repo1_status: dict[str, object] | None = None
    if args.repository_1 is not None:
        repo1 = args.repository_1.resolve()
        repo1_status = {
            "path": str(repo1),
            "exists": repo1.is_dir(),
            "pyproject_exists": (repo1 / "pyproject.toml").is_file(),
        }
        if not repo1_status["exists"] or not repo1_status["pyproject_exists"]:
            missing.append("repository_1_checkout")

    report = {
        "profile": args.profile,
        "python": sys.version,
        "executable": sys.executable,
        "passes": not missing,
        "missing": missing,
        "modules": results,
        "repository_1": repo1_status,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if not missing else 1)


if __name__ == "__main__":
    main()
