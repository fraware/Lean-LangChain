from __future__ import annotations

import json
from pathlib import Path

from obligation_runtime_schemas.environment import EnvironmentFingerprint
from obligation_runtime_schemas.obligation import Obligation
from obligation_runtime_schemas.interactive import InteractiveCheckResult
from obligation_runtime_schemas.policy import PolicyDecision
from obligation_runtime_schemas.witness import WitnessBundle

OUT = Path("packages/schemas/obligation_runtime_schemas/generated")
OUT.mkdir(parents=True, exist_ok=True)

MODELS = {
    "EnvironmentFingerprint": EnvironmentFingerprint,
    "Obligation": Obligation,
    "InteractiveCheckResult": InteractiveCheckResult,
    "PolicyDecision": PolicyDecision,
    "WitnessBundle": WitnessBundle,
}

for name, model in MODELS.items():
    path = OUT / f"{name}.schema.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(model.model_json_schema(), f, indent=2)
