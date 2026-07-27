from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, cast

import yaml


def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value: Any = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping in {path}")
    return cast(dict[str, Any], value)


def rows(card: dict[str, Any]) -> dict[str, tuple[float, float, str]]:
    categories: Any = card.get("categories")
    if not isinstance(categories, list):
        raise ValueError("scorecard categories must be a list")

    result: dict[str, tuple[float, float, str]] = {}
    for raw_category in categories:
        if not isinstance(raw_category, dict):
            raise ValueError("each scorecard category must be a mapping")
        category = cast(dict[str, Any], raw_category)
        name = str(category["name"])
        weight = float(category["weight"])
        score = float(category["score"])
        evidence = str(category.get("evidence", ""))
        if not 0 <= score <= 5:
            raise ValueError(f"Score for {name} must be 0..5")
        result[name] = (weight, score, evidence)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("scorecard_a", type=Path)
    parser.add_argument("scorecard_b", type=Path)
    args = parser.parse_args()
    a = load(args.scorecard_a)
    b = load(args.scorecard_b)
    a_rows = rows(a)
    b_rows = rows(b)
    names = list(dict.fromkeys([*a_rows, *b_rows]))

    print(f"# Repository comparison: {a['repository']} vs {b['repository']}\n")
    print("| Category | Weight | A | B | Delta B-A |")
    print("|---|---:|---:|---:|---:|")
    total_a = total_b = total_weight = 0.0
    for name in names:
        wa, sa, _ = a_rows.get(name, (0.0, 0.0, ""))
        wb, sb, _ = b_rows.get(name, (0.0, 0.0, ""))
        weight = max(wa, wb)
        total_weight += weight
        weighted_a = weight * sa / 5.0
        weighted_b = weight * sb / 5.0
        total_a += weighted_a
        total_b += weighted_b
        print(f"| {name} | {weight:.0f} | {sa:.1f} | {sb:.1f} | {sb - sa:+.1f} |")
    print(
        f"| **Total** | **{total_weight:.0f}** | **{total_a:.1f}** | "
        f"**{total_b:.1f}** | **{total_b - total_a:+.1f}** |"
    )


if __name__ == "__main__":
    main()
