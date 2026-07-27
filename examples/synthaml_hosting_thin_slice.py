"""Run the dependency-light SynthAML hosting proof from a source checkout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mle_platform.projects.synthaml.thin_slice import (
    DEFAULT_CONTRACT_PATH,
    run,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path(".artifacts/synthaml-hosting-thin-slice"),
    )
    parser.add_argument(
        "--feature-contract",
        type=Path,
        default=DEFAULT_CONTRACT_PATH,
    )
    args = parser.parse_args()
    result = run(
        args.output_directory.resolve(),
        contract_path=args.feature_contract.resolve(),
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
