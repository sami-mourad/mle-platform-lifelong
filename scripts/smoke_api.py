from __future__ import annotations

import argparse
import json

import httpx


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--force-fallback", action="store_true")
    args = parser.parse_args()

    readiness = httpx.get(f"{args.base_url}/health/ready", timeout=10.0)
    readiness.raise_for_status()
    payload = readiness.json()
    print("readiness:", json.dumps(payload, indent=2))

    request = {"features": {f"attr{i}": float(i) / 10.0 for i in range(1, 7)}}
    headers = {"x-request-id": "smoke-test"}
    if args.force_fallback:
        headers["x-force-fallback"] = "true"
    response = httpx.post(
        f"{args.base_url}/v1/score",
        json=request,
        headers=headers,
        timeout=10.0,
    )
    response.raise_for_status()
    result = response.json()
    print("prediction:", json.dumps(result, indent=2))

    expected_source = (
        "fallback" if args.force_fallback and payload["learned_model_loaded"] else None
    )
    if expected_source and result["model_source"] != expected_source:
        raise SystemExit(f"Expected {expected_source}, got {result['model_source']}")
    if result["decision"] not in {"clear", "review"}:
        raise SystemExit("Invalid decision")


if __name__ == "__main__":
    main()
