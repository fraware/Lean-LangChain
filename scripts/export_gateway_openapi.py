#!/usr/bin/env python3
"""Write Lean Gateway OpenAPI 3 schema to contracts/openapi/lean-gateway.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "apps" / "lean-gateway"))


# Ensure app can import without production-only env (conftest-style doubles optional).
def main() -> int:
    from obligation_runtime_lean_gateway.api.app import create_app

    app = create_app()
    schema = app.openapi()
    out = _REPO / "contracts" / "openapi" / "lean-gateway.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
