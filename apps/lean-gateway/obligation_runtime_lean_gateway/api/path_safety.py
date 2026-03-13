"""Path traversal safety for user-controlled file paths. File operations must be safe against traversal."""

from __future__ import annotations

from pathlib import Path


def resolve_under_root(root: Path, rel_path: str) -> Path:
    """
    Resolve a relative path under root and ensure it stays inside root.
    Raises ValueError if the resolved path escapes root (e.g. via '..').
    """
    root_resolved = root.resolve()
    combined = (root_resolved / rel_path).resolve()
    try:
        combined.relative_to(root_resolved)
    except ValueError:
        raise ValueError(f"Path escapes workspace: {rel_path!r}") from None
    return combined
