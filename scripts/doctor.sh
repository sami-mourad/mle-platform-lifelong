#!/usr/bin/env bash
set -euo pipefail

failed=0
for command in python docker git; do
  if command -v "$command" >/dev/null 2>&1; then
    printf 'ok   %-12s %s\n' "$command" "$(command -v "$command")"
  else
    printf 'miss %-12s\n' "$command"
    failed=1
  fi
done

python - <<'PY'
import sys
print(f"ok   python       {sys.version.split()[0]}")
if sys.version_info < (3, 12):
    raise SystemExit("Python 3.12+ is required")
PY

if command -v docker >/dev/null 2>&1; then
  docker compose version
fi

exit "$failed"
