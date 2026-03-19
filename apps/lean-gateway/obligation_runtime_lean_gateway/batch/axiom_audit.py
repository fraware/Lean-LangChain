"""Axiom audit for acceptance lane. Production uses AxiomAuditorReal (OBR_USE_REAL_AXIOM_AUDIT); AxiomAuditor is for test double injection only."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from obligation_runtime_schemas.batch import AxiomAuditResult, AxiomDependency

from obligation_runtime_lean_gateway.server.worker_runner import DEFAULT_WALL_CLOCK_SECONDS

if TYPE_CHECKING:
    from obligation_runtime_lean_gateway.server.runner import LeanRunner

# When test double (AxiomAuditor) is used, include this reason so clients know evidence is not real.
# Value kept for API compatibility; use constant name for code.
NON_REAL_AXIOM_AUDIT_REASON = "axiom_audit_stub_unconfigured"


def _axiom_timeout_seconds() -> float:
    """Timeout for axiom audit subprocess; OBR_AXIOM_AUDIT_TIMEOUT env for tests."""
    env = os.environ.get("OBR_AXIOM_AUDIT_TIMEOUT")
    if env is not None:
        try:
            return float(env)
        except ValueError:
            pass
    return min(60.0, DEFAULT_WALL_CLOCK_SECONDS)


class AxiomAuditor:
    """Test double only: returns ok=True but adds NON_REAL_AXIOM_AUDIT_REASON. Production uses AxiomAuditorReal; inject this only in tests."""

    def run(self, workspace_path: Path, declarations: list[str]) -> AxiomAuditResult:
        return AxiomAuditResult(
            ok=True,
            trust_level="clean",
            blocked_reasons=[NON_REAL_AXIOM_AUDIT_REASON],
            dependencies=[],
        )


class AxiomAuditorReal:
    """Real axiom audit: runs a command in the workspace and maps result to AxiomAuditResult.

    Command from OBR_AXIOM_AUDIT_CMD (default: lake build). Optional LeanRunner for
    container execution; on timeout or non-zero exit returns ok=False and blocked_reasons.
    """

    def __init__(
        self,
        timeout_seconds: float | None = None,
        runner: LeanRunner | None = None,
    ) -> None:
        self._timeout = timeout_seconds if timeout_seconds is not None else _axiom_timeout_seconds()
        cmd_env = os.environ.get("OBR_AXIOM_AUDIT_CMD")
        self._cmd = cmd_env.split() if cmd_env else ["lake", "build"]
        self._runner = runner

    def run(self, workspace_path: Path, declarations: list[str]) -> AxiomAuditResult:
        workspace_path = Path(workspace_path)
        if self._runner is not None:
            stdout, stderr, returncode, _ = self._runner.run(
                workspace_path, self._cmd, self._timeout
            )
            if returncode != 0:
                return AxiomAuditResult(
                    ok=False,
                    trust_level="blocked",
                    blocked_reasons=[stderr or stdout or "Axiom audit failed"],
                    dependencies=[],
                )
            deps = _parse_axiom_stdout(stdout, declarations)
            return AxiomAuditResult(
                ok=True,
                trust_level="clean",
                blocked_reasons=[],
                dependencies=deps,
            )
        try:
            result = subprocess.run(
                self._cmd,
                cwd=str(workspace_path),
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except subprocess.TimeoutExpired:
            return AxiomAuditResult(
                ok=False,
                trust_level="blocked",
                blocked_reasons=[f"Axiom audit exceeded {self._timeout}s"],
                dependencies=[],
            )
        except OSError as e:
            return AxiomAuditResult(
                ok=False,
                trust_level="blocked",
                blocked_reasons=[str(e)],
                dependencies=[],
            )
        if result.returncode != 0:
            return AxiomAuditResult(
                ok=False,
                trust_level="blocked",
                blocked_reasons=[result.stderr or result.stdout or "Axiom audit failed"],
                dependencies=[],
            )
        dependencies = _parse_axiom_stdout(result.stdout or "", declarations)
        return AxiomAuditResult(
            ok=True,
            trust_level="clean",
            blocked_reasons=[],
            dependencies=dependencies,
        )


def _parse_axiom_stdout(stdout: str, declarations: list[str]) -> list[AxiomDependency]:
    """Parse stdout for 'declaration: axiom1, axiom2' lines; return AxiomDependency list."""
    deps: list[AxiomDependency] = []
    for line in stdout.strip().splitlines():
        line = line.strip()
        if ":" in line:
            decl, _, rest = line.partition(":")
            axioms = [a.strip() for a in rest.split(",") if a.strip()]
            deps.append(AxiomDependency(declaration=decl.strip(), axioms=axioms))
    return deps
