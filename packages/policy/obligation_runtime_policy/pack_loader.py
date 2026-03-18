"""Load PolicyPack from YAML by name or path (plugin contract v1).

See docs/architecture/plugin-contract.md for the full versioned contract, schema,
and stability notes. Built-in packs live in packs/; external packs via path or
load_pack_from_path. Set OBR_POLICY_PACK to a pack name or absolute path.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from .models import PolicyPack

_PACKS_DIR = Path(__file__).resolve().parent / "packs"


def load_pack_from_path(path: Path) -> PolicyPack:
    """Load a policy pack from a filesystem path (plugin contract: any YAML conforming to PolicyPack)."""
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"Policy pack path not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return PolicyPack.model_validate(raw)


def load_pack(name: str) -> PolicyPack:
    """Load a policy pack by name or path. Name can be a built-in (e.g. strict_patch_gate_v1)
    or an absolute path / path containing os.sep to a .yaml file (external pack)."""
    if os.sep in name or Path(name).is_absolute():
        path = Path(name)
        if not path.suffix:
            path = path.with_suffix(".yaml")
        return load_pack_from_path(path)
    path = _PACKS_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Policy pack not found: {name}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return PolicyPack.model_validate(raw)


def list_packs() -> list[str]:
    """Return names of available built-in packs (without .yaml)."""
    if not _PACKS_DIR.exists():
        return []
    return [p.stem for p in _PACKS_DIR.glob("*.yaml")]
