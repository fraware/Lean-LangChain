"""Load PolicyPack from YAML by name or path (plugin contract v1 / v1.1).

See docs/architecture/plugin-contract.md for the versioned contract.
Built-in packs live in packs/; external packs via path. Composition:
  extends: <pack_name>   — merge base pack first (single inheritance)
  import: [<name>, ...]  — merge each listed pack in order (later overwrites)
Own keys override merged bases. Set OBR_POLICY_PACK to a pack name or absolute path.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from .models import PolicyPack

_PACKS_DIR = Path(__file__).resolve().parent / "packs"
# Scalars compared when composition_conflict_policy is error_on_import_scalar_override.
_IMPORT_SCALAR_KEYS: frozenset[str] = frozenset(
    {
        "allow_trust_compiler",
        "block_sorry_ax",
        "block_unexpected_custom_axioms",
        "require_human_if_imports_change",
        "require_human_on_trust_delta",
        "allow_interactive_warnings",
        "single_owner_handoff",
        "reviewer_gated_execution",
        "lock_ownership_invariant",
        "evidence_complete_execution_token",
        "delegation_admissibility",
        "state_transition_preservation",
        "artifact_admissibility",
        "side_effect_authorization",
    }
)
_MAX_COMPOSITION_DEPTH = 12
# Entry path/name -> merged raw dict (for repeated load_pack calls)
_merged_cache: dict[str, dict[str, Any]] = {}


def clear_pack_resolution_cache() -> None:
    """Test helper: drop merged pack cache."""
    _merged_cache.clear()


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Policy pack must be a YAML mapping: {path}")
    return raw


def _entry_key(name: str) -> str:
    if os.sep in name or Path(name).is_absolute():
        p = Path(name)
        if not p.suffix:
            p = p.with_suffix(".yaml")
        return str(p.resolve())
    return name


def _import_scalar_conflict(
    merged: dict[str, Any], incoming: dict[str, Any], import_name: str
) -> None:
    for k in _IMPORT_SCALAR_KEYS:
        if k not in merged or k not in incoming:
            continue
        if merged[k] != incoming[k]:
            raise ValueError(
                "Policy pack composition_conflict_policy=error_on_import_scalar_override: "
                f"import {import_name!r} sets {k!r}={incoming[k]!r} but earlier merge has {merged[k]!r}"
            )


def _resolve_path_for_name(name: str) -> Path:
    if os.sep in name or Path(name).is_absolute():
        p = Path(name)
        if not p.suffix:
            p = p.with_suffix(".yaml")
        return p.resolve()
    return (_PACKS_DIR / f"{name}.yaml").resolve()


def _merge_pack_layers(name: str, *, depth: int, visiting: set[str]) -> dict[str, Any]:
    if depth > _MAX_COMPOSITION_DEPTH:
        raise ValueError(
            f"Policy pack composition depth exceeded ({_MAX_COMPOSITION_DEPTH}): check extends/import"
        )
    path = _resolve_path_for_name(name)
    key = str(path)
    if key in visiting:
        raise ValueError(f"Circular policy pack reference involving {key}")
    visiting.add(key)
    try:
        if not path.exists():
            raise FileNotFoundError(f"Policy pack not found: {name} ({path})")
        raw = _read_yaml_mapping(path)
        merged: dict[str, Any] = {}
        ext = raw.get("extends")
        imports = raw.get("import") or []
        if ext:
            if not isinstance(ext, str):
                raise TypeError("extends must be a pack name string")
            sub = _merge_pack_layers(ext, depth=depth + 1, visiting=visiting)
            merged.update(sub)
        strict_imports = raw.get("composition_conflict_policy") == "error_on_import_scalar_override"
        if isinstance(imports, list):
            for imp in imports:
                if not isinstance(imp, str):
                    continue
                sub = _merge_pack_layers(imp, depth=depth + 1, visiting=visiting)
                if strict_imports:
                    _import_scalar_conflict(merged, sub, imp)
                merged.update(sub)
        body = {k: v for k, v in raw.items() if k not in ("extends", "import")}
        merged.update(body)
        return merged
    finally:
        visiting.discard(key)


def _merged_dict_for_entry(entry: str) -> dict[str, Any]:
    cache_key = _entry_key(entry)
    if cache_key in _merged_cache:
        return dict(_merged_cache[cache_key])
    # Built-in single-file packs without extends/import: fast path
    path = _resolve_path_for_name(entry)
    if not path.exists():
        raise FileNotFoundError(f"Policy pack not found: {entry}")
    raw = _read_yaml_mapping(path)
    if raw.get("extends") is None and not raw.get("import"):
        merged = dict(raw)
    else:
        merged = _merge_pack_layers(entry, depth=0, visiting=set())
    _merged_cache[cache_key] = dict(merged)
    return merged


def load_pack_from_path(path: Path) -> PolicyPack:
    """Load from filesystem path; supports extends/import relative to built-in names."""
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"Policy pack path not found: {path}")
    merged = _merged_dict_for_entry(str(path))
    return PolicyPack.model_validate(merged)


def load_pack(name: str) -> PolicyPack:
    """Load by built-in name, absolute path, or path with separator (see module docstring)."""
    return load_pack_from_path(_resolve_path_for_name(name))


def list_packs() -> list[str]:
    """Return names of available built-in packs (without .yaml)."""
    if not _PACKS_DIR.exists():
        return []
    return [p.stem for p in _PACKS_DIR.glob("*.yaml")]
