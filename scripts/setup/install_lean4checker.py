#!/usr/bin/env python3
"""Build lean4checker from source and print OBR_FRESH_CHECK_CMD for the current session.

Requires: git, lake (elan/Lean 4) in PATH. Clones to repo_root/.var/lean4checker and runs
lake build. Use the printed export to set OBR_FRESH_CHECK_CMD so the Gateway/CI can run
the fresh checker without installing lean4checker globally.

Usage:
  python scripts/setup/install_lean4checker.py
  # Then: set OBR_FRESH_CHECK_CMD=<printed path> --fresh
  # Or add .var/lean4checker/.lake/bin to PATH (and set OBR_USE_REAL_FRESH_CHECKER=1).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


REPO = "https://github.com/leanprover/lean4checker.git"
DEFAULT_DIR = ".var/lean4checker"


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent.parent
    dest = repo_root / DEFAULT_DIR

    if not shutil.which("lake"):
        print("lake not in PATH; install elan and Lean 4 first.", file=sys.stderr)
        return 1
    if not shutil.which("git"):
        print("git not in PATH.", file=sys.stderr)
        return 1

    dest.mkdir(parents=True, exist_ok=True)

    if not (dest / ".git").exists():
        print(f"Cloning lean4checker into {dest}...")
        r = subprocess.run(
            ["git", "clone", "--depth", "1", REPO, str(dest)],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            print(r.stderr or r.stdout, file=sys.stderr)
            return 1

    print("Building lean4checker (lake build)...")
    r = subprocess.run(
        ["lake", "build"],
        cwd=str(dest),
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(r.stderr or r.stdout, file=sys.stderr)
        return 1

    # Lake puts exe in .lake/build/bin/ (or .lake/bin/ on some versions)
    for bin_dir in [dest / ".lake" / "build" / "bin", dest / ".lake" / "bin"]:
        exe_name = "lean4checker.exe" if sys.platform == "win32" else "lean4checker"
        exe = bin_dir / exe_name
        if exe.exists():
            break
        candidates = list(bin_dir.glob("*.exe")) if sys.platform == "win32" else list(bin_dir.glob("*"))
        if candidates:
            exe = candidates[0]
            break
    else:
        print("No executable found under .lake/build/bin or .lake/bin", file=sys.stderr)
        return 1

    exe_path = exe.resolve()
    print("")
    print("lean4checker built successfully.")
    print("To run the fresh checker, set in this shell (or in Gateway env):")
    if sys.platform == "win32":
        print(f'  $env:OBR_FRESH_CHECK_CMD = "{exe_path} --fresh"')
    else:
        print(f'  export OBR_FRESH_CHECK_CMD="{exe_path} --fresh"')
    print("Then set OBR_USE_REAL_FRESH_CHECKER=1 and run the Gateway or tests.")
    print("")
    print("Or add the bin dir to PATH so 'lean4checker' is found:")
    print(f"  {bin_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
