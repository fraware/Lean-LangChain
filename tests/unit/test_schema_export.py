"""Unit tests for schema JSON export. Ensures schemas export cleanly for CI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

EXPECTED_SCHEMAS = (
    "AcceptanceSummary",
    "EnvironmentFingerprint",
    "Obligation",
    "InteractiveCheckResult",
    "PolicyDecision",
    "WitnessBundle",
)


def test_export_json_schemas_produces_valid_files() -> None:
    """Running the export script produces expected schema files with valid JSON."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    script = repo_root / "scripts" / "export_json_schemas.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (result.stdout or "") + (result.stderr or "")

    out_dir = repo_root / "packages" / "schemas" / "obligation_runtime_schemas" / "generated"
    assert out_dir.is_dir(), f"Expected directory {out_dir}"

    for name in EXPECTED_SCHEMAS:
        path = out_dir / f"{name}.schema.json"
        assert path.exists(), f"Expected {path}"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict), f"{name}.schema.json must be a JSON object"
