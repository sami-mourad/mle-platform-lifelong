from __future__ import annotations

import subprocess
import sys


def audit_main() -> None:
    raise SystemExit(
        subprocess.call([sys.executable, "tools/repo_audit.py", ".", "--format", "markdown"])
    )
