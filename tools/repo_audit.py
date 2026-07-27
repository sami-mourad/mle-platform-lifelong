from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    evidence: str
    weight: int


EXPECTED = {
    "packaging": ["pyproject.toml"],
    "container": ["infra/docker/Dockerfile", "docker-compose.yml"],
    "orchestration": ["src/mle_platform/orchestration/definitions.py"],
    "tests": ["tests/unit", "tests/integration", "tests/contract", "tests/synthaml_overlay"],
    "ci": [".github/workflows/ci.yml"],
    "docs": ["docs/README.md", "docs/architecture/OVERVIEW.md", "VALIDATION.md"],
    "infra_as_code": ["infra/terraform/aws/main.tf"],
    "runbook": ["docs/guides/SYNTHAML_DEMO.md", "docs/operations/RUNBOOK.md"],
}

IGNORED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    ".artifacts",
    ".data",
    "build",
    "dist",
}
SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]


def is_generated(path: Path) -> bool:
    return bool(IGNORED_PARTS.intersection(path.parts))


def module_package_collisions(root: Path) -> list[str]:
    collisions: list[str] = []
    for source_root in [root / "src", root / "tests", root / "tools", root / "examples"]:
        if not source_root.exists():
            continue
        for module in source_root.rglob("*.py"):
            if module.name == "__init__.py":
                continue
            package = module.with_suffix("")
            if package.is_dir() and (package / "__init__.py").is_file():
                collisions.append(str(module.relative_to(root)))
    return collisions


def audit(root: Path) -> list[Check]:
    checks: list[Check] = []
    for name, expected_paths in EXPECTED.items():
        missing = [path for path in expected_paths if not (root / path).exists()]
        evidence = "missing=" + ",".join(missing) if missing else "present"
        checks.append(Check(name, not missing, evidence, 8))

    python_files = list((root / "src").rglob("*.py")) if (root / "src").exists() else []
    typed = sum("->" in path.read_text(errors="ignore") for path in python_files)
    checks.append(
        Check(
            "type_hints",
            typed >= max(1, len(python_files) // 2),
            f"typed_files={typed}/{len(python_files)}",
            8,
        )
    )

    collisions = module_package_collisions(root)
    checks.append(
        Check("no_module_package_collisions", not collisions, f"collisions={collisions}", 10)
    )

    large_files = [
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file() and path.stat().st_size > 5 * 1024 * 1024 and not is_generated(path)
    ]
    checks.append(Check("no_large_committed_files", not large_files, f"large={large_files}", 5))

    secret_hits: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or is_generated(path) or path.stat().st_size > 1_000_000:
            continue
        text = path.read_text(errors="ignore")
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            secret_hits.append(str(path.relative_to(root)))
    checks.append(Check("no_obvious_secrets", not secret_hits, f"hits={secret_hits}", 10))
    return checks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    args = parser.parse_args()
    checks = audit(args.root.resolve())
    possible = sum(check.weight for check in checks)
    achieved = sum(check.weight for check in checks if check.passed)
    payload = {
        "score": achieved,
        "possible": possible,
        "passes": achieved == possible,
        "checks": [asdict(c) for c in checks],
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(f"# Repository audit: {achieved}/{possible}\n")
        print("| Check | Result | Weight | Evidence |")
        print("|---|---:|---:|---|")
        for check in checks:
            print(
                f"| {check.name} | {'PASS' if check.passed else 'FAIL'} | {check.weight} | {check.evidence} |"
            )
    raise SystemExit(0 if payload["passes"] else 1)


if __name__ == "__main__":
    main()
