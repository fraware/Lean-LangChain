from __future__ import annotations

import hashlib


def summarize_patch(
    before: dict[str, str], after: dict[str, str], protected_paths: list[str] | None = None
) -> dict[str, object]:
    protected_paths = protected_paths or []
    changed_files = sorted(set(before) | set(after))
    imports_changed = False
    for path in changed_files:
        b = before.get(path, "")
        a = after.get(path, "")
        if b != a and ("import " in b or "import " in a):
            imports_changed = True
            break
    protected_touched = [p for p in changed_files if p in protected_paths]
    diff_hash = hashlib.sha256(
        ("".join(after.get(p, "") for p in changed_files)).encode()
    ).hexdigest()
    return {
        "changed_files": changed_files,
        "imports_changed": imports_changed,
        "protected_paths_touched": protected_touched,
        "diff_hash": diff_hash,
    }
