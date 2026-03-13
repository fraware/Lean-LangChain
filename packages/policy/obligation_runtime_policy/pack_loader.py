"""Load PolicyPack from YAML by name."""

from __future__ import annotations

from pathlib import Path

import yaml

from .models import PolicyPack

_PACKS_DIR = Path(__file__).resolve().parent / "packs"


def load_pack(name: str) -> PolicyPack:
    """Load a policy pack by name (e.g. strict_patch_gate_v1). Looks up packs/<name>.yaml."""
    path = _PACKS_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Policy pack not found: {name}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return PolicyPack.model_validate(raw)


def list_packs() -> list[str]:
    """Return names of available packs (without .yaml)."""
    if not _PACKS_DIR.exists():
        return []
    return [p.stem for p in _PACKS_DIR.glob("*.yaml")]
