#!/usr/bin/env python3
"""
Export the FastAPI OpenAPI document for this backend.

Notes:
- The backend generates OpenAPI dynamically from the actual registered routes.
- This exporter intentionally enables FAST_TEST_MODE by default to avoid heavy startup.
- If DATABASE_URL is not set, a local placeholder is used so `main.py` can import.

Usage:
  python3 scripts/python/export_openapi.py openapi.json
  FAST_TEST_MODE=1 BRAINOPS_ALLOW_OFFLINE_AUTH=true DATABASE_URL=... python3 scripts/python/export_openapi.py openapi.json
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Tuple


DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"


def _count_operations(openapi: Dict[str, Any]) -> Tuple[int, int]:
    paths = openapi.get("paths") or {}
    path_count = len(paths)
    op_count = 0
    for methods in paths.values():
        if not isinstance(methods, dict):
            continue
        for method, spec in methods.items():
            if method.lower() in {"get", "post", "put", "patch", "delete", "options", "head"} and isinstance(
                spec, dict
            ):
                op_count += 1
    return path_count, op_count


def main() -> int:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None

    os.environ.setdefault("FAST_TEST_MODE", "1")
    os.environ.setdefault("BRAINOPS_ALLOW_OFFLINE_AUTH", "true")
    os.environ.setdefault("DATABASE_URL", DEFAULT_DATABASE_URL)

    # Import after env vars are configured.
    import main as brainops_main  # type: ignore

    openapi = brainops_main.app.openapi()
    path_count, op_count = _count_operations(openapi)

    if out_path is None:
        json.dump(openapi, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(openapi, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    sys.stderr.write(f"Exported OpenAPI: {path_count} paths, {op_count} operations\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

