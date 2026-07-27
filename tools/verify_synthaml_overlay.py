"""Rerunnable source verifier for the SynthAML overlay."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
RUNTIME_PARTS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}


def _module_package_collisions() -> list[str]:
    collisions: list[str] = []
    for source_root in [ROOT / "src", ROOT / "tests", ROOT / "tools", ROOT / "examples"]:
        if not source_root.exists():
            continue
        for module in source_root.rglob("*.py"):
            if module.name == "__init__.py":
                continue
            package = module.with_suffix("")
            if package.is_dir() and (package / "__init__.py").is_file():
                collisions.append(str(module.relative_to(ROOT)))
    return collisions


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict-artifacts", action="store_true")
    args = parser.parse_args()
    issues: list[str] = []
    python_files = [
        *ROOT.glob("src/**/*.py"),
        *ROOT.glob("tests/**/*.py"),
        *ROOT.glob("examples/*.py"),
        *ROOT.glob("tools/*.py"),
    ]
    for path in python_files:
        try:
            ast.parse(path.read_text(), filename=str(path))
        except SyntaxError as error:
            issues.append(f"{path.relative_to(ROOT)}: {error}")
    json_files = list(ROOT.glob("contracts/synthaml/*.json"))
    for path in json_files:
        try:
            json.loads(path.read_text())
        except json.JSONDecodeError as error:
            issues.append(f"{path.relative_to(ROOT)}: {error}")
    for collision in _module_package_collisions():
        issues.append(f"module/package collision: {collision}")
    if args.strict_artifacts:
        for path in ROOT.rglob("*"):
            if path.is_file() and (RUNTIME_PARTS.intersection(path.parts) or path.suffix == ".pyc"):
                issues.append(f"runtime debris: {path.relative_to(ROOT)}")
    print(
        json.dumps(
            {
                "python_file_count": len(python_files),
                "json_contract_count": len(json_files),
                "strict_artifacts": args.strict_artifacts,
                "issues": issues,
            },
            indent=2,
        )
    )
    raise SystemExit(1 if issues else 0)


if __name__ == "__main__":
    main()
