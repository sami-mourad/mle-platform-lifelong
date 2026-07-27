"""Run bounded SynthAML evidence gates in isolated subprocesses."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).parents[1].resolve()


@dataclass(frozen=True)
class GateResult:
    name: str
    command: list[str]
    returncode: int
    log_path: str


def _checkout_path(argument: Path) -> Path:
    """Resolve a checkout argument relative to the Repository 2 root."""
    return argument.resolve() if argument.is_absolute() else (ROOT / argument).resolve()


def _correct_repository_1_spelling(argument: Path | None) -> Path | None:
    """Correct a common checkout-name mix-up without changing Python imports.

    The Git repository is named ``temporal-mle-data-contract`` while its import
    package is ``temporal_mle``. Older local instructions sometimes used the
    non-existent checkout name ``temporal_mle_data_contract``.
    """
    if argument is None or _checkout_path(argument).is_dir():
        return argument

    alternatives: list[Path] = []
    if "_" in argument.name:
        alternatives.append(argument.with_name(argument.name.replace("_", "-")))
    if "-" in argument.name:
        alternatives.append(argument.with_name(argument.name.replace("-", "_")))

    for candidate in alternatives:
        checkout = _checkout_path(candidate)
        if checkout.is_dir() and (checkout / "pyproject.toml").is_file():
            print(f"[repository_1] corrected checkout path: {argument} -> {candidate}")
            return candidate
    return argument


def _align_snapshot_with_repository(
    snapshot: Path | None,
    *,
    requested_repository: Path | None,
    resolved_repository: Path | None,
) -> Path | None:
    """Move a snapshot path under an auto-corrected Repository 1 checkout."""
    if (
        snapshot is None
        or requested_repository is None
        or resolved_repository is None
        or requested_repository == resolved_repository
        or _checkout_path(snapshot).is_file()
    ):
        return snapshot

    try:
        suffix = snapshot.relative_to(requested_repository)
    except ValueError:
        return snapshot

    candidate = resolved_repository / suffix
    if _checkout_path(candidate).is_file():
        print(f"[repository_1] corrected snapshot path: {snapshot} -> {candidate}")
        return candidate
    return snapshot


def _public_path(path: Path) -> str:
    """Return a repository-relative path when possible."""
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def _public_command(command: Sequence[str]) -> list[str]:
    """Sanitize machine-specific executables and checkout paths in summaries."""
    public: list[str] = []
    for index, value in enumerate(command):
        if index == 0 and Path(value).resolve() == Path(sys.executable).resolve():
            public.append("python")
            continue
        candidate = Path(value)
        if candidate.is_absolute():
            public.append(_public_path(candidate))
        else:
            public.append(value)
    return public


def _run(name: str, command: Sequence[str], output: Path) -> GateResult:
    log = output / f"{name}.txt"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT / "src"), environment.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    completed = subprocess.run(
        list(command),
        cwd=ROOT,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    log.write_text(completed.stdout)
    print(f"[{name}] {'PASS' if completed.returncode == 0 else 'FAIL'} -> {log}")
    if completed.stdout:
        print(completed.stdout.rstrip())
    return GateResult(
        name,
        _public_command(command),
        completed.returncode,
        _public_path(log),
    )


def _core_commands(python: str, output: Path) -> list[tuple[str, list[str]]]:
    thin_output = output / "thin_slice_artifacts"
    dependency_light_tests = [
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "tests/synthaml_overlay/test_evidently_drift_count.py",
        "tests/synthaml_overlay/test_fastapi_service.py",
        "tests/synthaml_overlay/test_feature_contract.py",
        "tests/synthaml_overlay/test_feature_retrieval.py",
        "tests/synthaml_overlay/test_hosting_thin_slice.py",
        "tests/synthaml_overlay/test_monitoring_policy.py",
        "tests/synthaml_overlay/test_observation_store.py",
        "tests/synthaml_overlay/test_orchestration_boundaries.py",
        "tests/synthaml_overlay/test_promotion_policy.py",
        "tests/synthaml_overlay/test_release_manifest.py",
        "tests/synthaml_overlay/test_release_controller.py",
        "tests/synthaml_overlay/test_serving_application.py",
    ]
    return [
        (
            "00_environment_core",
            [python, "tools/check_synthaml_environment.py", "--profile", "core"],
        ),
        (
            "01_compile",
            [python, "-m", "compileall", "-q", "src", "examples", "tests", "tools"],
        ),
        ("02_overlay_verify", [python, "tools/verify_synthaml_overlay.py"]),
        (
            "03_repository_audit",
            [python, "tools/repo_audit.py", ".", "--format", "json"],
        ),
        ("04_core_tests", [python, "-m", "pytest", "-ra", *dependency_light_tests]),
        (
            "05_hosting_thin_slice",
            [
                python,
                "examples/synthaml_hosting_thin_slice.py",
                "--output-directory",
                str(thin_output),
            ],
        ),
    ]


def _bridge_commands(
    python: str,
    repository_1: Path | None,
    feature_snapshot: Path | None,
) -> list[tuple[str, list[str]]]:
    if repository_1 is None or feature_snapshot is None:
        raise ValueError("bridge gates require --repository-1 and --feature-snapshot")
    return [
        (
            "10_environment_bridge",
            [
                python,
                "tools/check_synthaml_environment.py",
                "--profile",
                "bridge",
                "--repository-1",
                str(repository_1),
            ],
        ),
        (
            "11_cross_repository_contract",
            [
                python,
                "tools/verify_cross_repository_contract.py",
                "--repository-1",
                str(repository_1),
                "--feature-snapshot",
                str(feature_snapshot),
            ],
        ),
    ]


def _sdk_commands(
    python: str,
    repository_1: Path | None,
    output: Path,
) -> list[tuple[str, list[str]]]:
    command = [python, "tools/check_synthaml_environment.py", "--profile", "sdk"]
    if repository_1 is not None:
        command.extend(["--repository-1", str(repository_1)])
    demo_output = output / "sdk_synthetic_release"
    return [
        ("20_environment_sdk", command),
        (
            "21_feast_boundary",
            [
                python,
                "-m",
                "pytest",
                "-ra",
                "tests/synthaml_overlay/test_feast_adapter_integration.py",
            ],
        ),
        (
            "22_mlflow_boundary",
            [
                python,
                "-m",
                "pytest",
                "-ra",
                "tests/synthaml_overlay/test_mlflow_training_integration.py",
            ],
        ),
        (
            "23_bentoml_boundary",
            [
                python,
                "-m",
                "pytest",
                "-ra",
                "tests/synthaml_overlay/test_bentoml_runtime_integration.py",
            ],
        ),
        (
            "24_evidently_boundary",
            [
                python,
                "-m",
                "pytest",
                "-ra",
                "tests/synthaml_overlay/test_monitoring_integration.py",
            ],
        ),
        (
            "25_sdk_release_demo",
            [
                python,
                "examples/synthaml_platform_overlay_demo.py",
                "--output-directory",
                str(demo_output),
            ],
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        choices=["core", "bridge", "sdk", "all"],
        default="core",
    )
    parser.add_argument("--repository-1", type=Path)
    parser.add_argument("--feature-snapshot", type=Path)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("evidence/current_validation"),
    )
    args = parser.parse_args()

    if args.output_directory.is_absolute():
        output = args.output_directory.resolve()
    else:
        output = (ROOT / args.output_directory).resolve()
    output.mkdir(parents=True, exist_ok=True)
    python = sys.executable

    requested_repository_1 = args.repository_1
    repository_1 = _correct_repository_1_spelling(requested_repository_1)
    feature_snapshot = _align_snapshot_with_repository(
        args.feature_snapshot,
        requested_repository=requested_repository_1,
        resolved_repository=repository_1,
    )

    commands: list[tuple[str, list[str]]] = []
    if args.profile in {"core", "all"}:
        commands.extend(_core_commands(python, output))
    if args.profile in {"bridge", "all"}:
        commands.extend(_bridge_commands(python, repository_1, feature_snapshot))
    if args.profile in {"sdk", "all"}:
        commands.extend(_sdk_commands(python, repository_1, output))

    results: list[GateResult] = []
    for name, command in commands:
        result = _run(name, command, output)
        results.append(result)
        if result.returncode != 0:
            break

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "profile": args.profile,
        "passes": (
            bool(results)
            and all(result.returncode == 0 for result in results)
            and len(results) == len(commands)
        ),
        "completed_gate_count": len(results),
        "planned_gate_count": len(commands),
        "results": [asdict(result) for result in results],
    }
    report_path = output / f"synthaml_{args.profile}_gate_summary.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(report_path)
    raise SystemExit(0 if report["passes"] else 1)


if __name__ == "__main__":
    main()
