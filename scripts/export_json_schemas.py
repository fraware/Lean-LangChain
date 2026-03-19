from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running from repo root without pip install -e (e.g. via make export-schemas)
_root = Path(__file__).resolve().parent.parent
for _p in (_root, _root / "packages" / "schemas"):
    if _p not in sys.path:
        sys.path.insert(0, str(_p))

try:
    from lean_langchain_schemas.environment import EnvironmentFingerprint
    from lean_langchain_schemas.obligation import Obligation
    from lean_langchain_schemas.interactive import InteractiveCheckResult
    from lean_langchain_schemas.policy import PolicyDecision
    from lean_langchain_schemas.witness import AcceptanceSummary, WitnessBundle
except ModuleNotFoundError as e:
    print(
        "export_json_schemas: missing dependency. Use the same Python that has the project installed.\n"
        "  Run: make install-dev-full  (or: python -m pip install -e packages/schemas)\n"
        "  Venv without pip: python -m ensurepip then python -m pip install -e packages/schemas\n"
        "  Windows venv: .\\.venv\\Scripts\\python -m pip install -e packages/schemas ...",
        file=sys.stderr,
    )
    raise SystemExit(1) from e

OUT = _root / "packages" / "schemas" / "lean_langchain_schemas" / "generated"
OUT.mkdir(parents=True, exist_ok=True)

MODELS = {
    "EnvironmentFingerprint": EnvironmentFingerprint,
    "Obligation": Obligation,
    "InteractiveCheckResult": InteractiveCheckResult,
    "PolicyDecision": PolicyDecision,
    "AcceptanceSummary": AcceptanceSummary,
    "WitnessBundle": WitnessBundle,
}

for name, model in MODELS.items():
    path = OUT / f"{name}.schema.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(model.model_json_schema(), f, indent=2)
