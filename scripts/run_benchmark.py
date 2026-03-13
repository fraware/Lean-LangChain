#!/usr/bin/env python3
"""Run pipeline and optional workload benchmark; report metrics (latency, counts, percentiles).

Usage:
  python scripts/run_benchmark.py              # pipeline only
  python scripts/run_benchmark.py --workload 5 # pipeline + 5 graph invocations
  python scripts/run_benchmark.py --output report.json

Metrics reported:
- Pipeline: lint_s, typecheck_s, schema_tests_s, unit_tests_s, unit_passed, unit_skipped,
  integration_tests_s, integration_passed, integration_skipped, regressions_s, regressions_passed,
  export_schemas_s, total_wall_s.
- Workload (if --workload N): graph_invocations, latency_ms_list, latency_p50_ms, latency_p95_ms,
  latency_p99_ms, throughput_per_s.
- Optional: slowest_tests (from pytest --durations).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _get_project_python(root: Path) -> str:
    """Prefer conda/venv Python so subprocesses use the project env when Make uses another."""
    conda = os.environ.get("CONDA_PREFIX")
    if conda:
        cand = root / ".venv"  # avoid using conda if we have venv in repo
        if not cand.is_dir():
            if sys.platform == "win32":
                py = Path(conda) / "python.exe"
            else:
                py = Path(conda) / "bin" / "python"
            if py.exists():
                return str(py)
    venv = root / ".venv"
    if venv.is_dir():
        if sys.platform == "win32":
            py = venv / "Scripts" / "python.exe"
        else:
            py = venv / "bin" / "python"
        if py.exists():
            return str(py)
    return sys.executable


def _run(cmd: list[str], cwd: Path, timeout: int = 300) -> tuple[float, int, str, str]:
    start = time.perf_counter()
    env = os.environ.copy()
    extra = [str(cwd), str(cwd / "packages" / "schemas")]
    env["PYTHONPATH"] = os.pathsep.join(extra + [env.get("PYTHONPATH", "")])
    out = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    elapsed = time.perf_counter() - start
    stdout = out.stdout or ""
    stderr = out.stderr or ""
    return elapsed, out.returncode, stdout, stderr


def _run_pipeline(metrics: dict, python_exe: str, skip_tests: bool = False) -> bool:
    root = _repo_root()
    ok = True

    # Lint
    t, code, _, _ = _run([python_exe, "-m", "ruff", "check", "."], root, timeout=60)
    metrics["lint_s"] = round(t, 3)
    metrics["lint_ok"] = code == 0
    if code != 0:
        ok = False

    # Typecheck
    t, code, _, _ = _run(
        [python_exe, "-m", "mypy", "packages/schemas", "apps/lean-gateway", "apps/orchestrator"],
        root,
        timeout=120,
    )
    metrics["typecheck_s"] = round(t, 3)
    metrics["typecheck_ok"] = code == 0
    if code != 0:
        ok = False

    if skip_tests:
        return ok

    # Schema tests
    t, code, out, err = _run(
        [python_exe, "-m", "pytest", "tests/unit/test_schema_roundtrip.py",
         "tests/unit/test_hash_stability.py", "tests/unit/test_schema_export.py", "-q", "--tb=no"],
        root,
        timeout=30,
    )
    metrics["schema_tests_s"] = round(t, 3)
    metrics["schema_tests_ok"] = code == 0
    _parse_pytest_summary(out + "\n" + err, metrics, "schema")
    if code != 0:
        ok = False

    # Unit tests
    t, code, out, err = _run(
        [python_exe, "-m", "pytest", "tests/unit", "-q", "--tb=no"],
        root,
        timeout=120,
    )
    metrics["unit_tests_s"] = round(t, 3)
    metrics["unit_tests_ok"] = code == 0
    _parse_pytest_summary(out + "\n" + err, metrics, "unit")
    if code != 0:
        ok = False

    # Integration tests
    t, code, out, err = _run(
        [python_exe, "-m", "pytest", "tests/integration", "-q", "--tb=no"],
        root,
        timeout=180,
    )
    metrics["integration_tests_s"] = round(t, 3)
    metrics["integration_tests_ok"] = code == 0
    _parse_pytest_summary(out + "\n" + err, metrics, "integration")
    if code != 0:
        ok = False

    # Regressions
    t, code, out, err = _run(
        [python_exe, "-m", "pytest", "tests/regressions", "-q", "--tb=no"],
        root,
        timeout=60,
    )
    metrics["regressions_s"] = round(t, 3)
    metrics["regressions_ok"] = code == 0
    _parse_pytest_summary(out + "\n" + err, metrics, "regressions")
    if code != 0:
        ok = False

    # Export schemas
    t, code, _, _ = _run(
        [python_exe, "scripts/export_json_schemas.py"],
        root,
        timeout=30,
    )
    metrics["export_schemas_s"] = round(t, 3)
    metrics["export_schemas_ok"] = code == 0
    if code != 0:
        ok = False

    return ok


def _parse_pytest_summary(out: str, metrics: dict, prefix: str) -> None:
    """Extract passed/skipped/failed from pytest -q output (e.g. '119 passed, 1 skipped in 30.65s')."""
    passed = skipped = failed = 0
    combined = out or ""
    for line in combined.splitlines():
        line = line.strip()
        if not line or "passed" not in line:
            continue
        parts = line.replace(",", " ").split()
        for i, p in enumerate(parts):
            if p == "passed" and i > 0:
                try:
                    passed = int(parts[i - 1])
                except (ValueError, IndexError):
                    pass
            elif p == "skipped" and i > 0:
                try:
                    skipped = int(parts[i - 1])
                except (ValueError, IndexError):
                    pass
            elif p == "failed" and i > 0:
                try:
                    failed = int(parts[i - 1])
                except (ValueError, IndexError):
                    pass
    if passed == 0 and "passed" in combined:
        m = re.search(r"(\d+)\s+passed", combined)
        if m:
            passed = int(m.group(1))
    metrics[f"{prefix}_passed"] = passed
    metrics[f"{prefix}_skipped"] = skipped
    metrics[f"{prefix}_failed"] = failed


def _run_workload(n: int, metrics: dict) -> None:
    """Run n graph invocations (TestClient), record latencies."""
    root = _repo_root()
    latencies_ms: list[float] = []
    try:
        from fastapi.testclient import TestClient
        from obligation_runtime_lean_gateway.api.app import create_app
        from obligation_runtime_orchestrator.runtime.graph import build_patch_admissibility_graph
        from obligation_runtime_orchestrator.runtime.initial_state import make_initial_state
        from obligation_runtime_sdk.client import ObligationRuntimeClient
    except ImportError:
        metrics["workload_skipped"] = "import failed"
        return

    repo_path = root / "tests" / "integration" / "fixtures" / "lean-mini"
    if not repo_path.is_dir():
        metrics["workload_skipped"] = "fixture not found"
        return

    app = create_app()
    with TestClient(app) as tc:
        def adapter(method: str, path: str, body):
            if method == "POST":
                r = tc.post(path, json=body if body is not None else {})
            else:
                r = tc.get(path)
            r.raise_for_status()
            return r.json()

        client = ObligationRuntimeClient(base_url="http://testserver", request_adapter=adapter)
        graph = build_patch_admissibility_graph(client=client)
        initial = make_initial_state(
            thread_id="bench",
            obligation_id="bench",
            obligation={"target": {"repo_id": "lean-mini"}, "environment_fingerprint": {}},
            target_files=["Mini/Basic.lean"],
            current_patch={"Mini/Basic.lean": "def x := 1\n"},
            repo_path=str(repo_path),
        )
        for _ in range(n):
            start = time.perf_counter()
            graph.invoke(initial)
            latencies_ms.append((time.perf_counter() - start) * 1000)

    latencies_ms.sort()
    metrics["workload_invocations"] = n
    metrics["workload_latency_ms"] = [round(x, 2) for x in latencies_ms]
    if latencies_ms:
        metrics["workload_latency_p50_ms"] = round(latencies_ms[int(len(latencies_ms) * 0.5)], 2)
        metrics["workload_latency_p95_ms"] = round(latencies_ms[min(int(len(latencies_ms) * 0.95), len(latencies_ms) - 1)], 2)
        metrics["workload_latency_p99_ms"] = round(latencies_ms[min(int(len(latencies_ms) * 0.99), len(latencies_ms) - 1)], 2)
        total_s = sum(latencies_ms) / 1000
        metrics["workload_throughput_per_s"] = round(n / total_s if total_s > 0 else 0, 4)


def _run_slowest_tests(metrics: dict, python_exe: str, n: int = 10) -> None:
    """Run pytest --durations=N to get slowest tests."""
    root = _repo_root()
    _, code, out, err = _run(
        [python_exe, "-m", "pytest", "tests/unit", "tests/integration", "tests/regressions",
         "-q", "--tb=no", f"--durations={n}"],
        root,
        timeout=300,
    )
    slowest: list[dict] = []
    for line in (out + "\n" + err).splitlines():
        line = line.strip()
        if line.startswith("(") or "passed" in line:
            continue
        if "s" in line and ("test_" in line or "tests/" in line):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    dur = float(parts[0].replace("s", ""))
                    name = " ".join(parts[1:])[:80]
                    slowest.append({"duration_s": round(dur, 3), "test": name})
                except ValueError:
                    pass
    metrics["slowest_tests"] = slowest[:n]


def main() -> int:
    root = _repo_root()
    for p in (
        root,
        root / "packages" / "schemas",
        root / "packages" / "sdk-py",
        root / "apps" / "lean-gateway",
        root / "apps" / "orchestrator",
    ):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)

    ap = argparse.ArgumentParser(description="Run benchmark and report metrics")
    ap.add_argument("--workload", type=int, default=0, help="Number of graph invocations for workload benchmark")
    ap.add_argument("--slowest", type=int, default=0, help="Report N slowest tests (0 = skip)")
    ap.add_argument("--output", "-o", default="", help="Write JSON report to file")
    ap.add_argument("--pipeline-only", action="store_true", help="Only run pipeline (lint, typecheck, tests)")
    args = ap.parse_args()

    python_exe = _get_project_python(root)
    metrics = {"benchmark": "obligation-runtime", "pipeline": {}}
    wall_start = time.perf_counter()

    ok = _run_pipeline(metrics, python_exe, skip_tests=False)
    total_wall = time.perf_counter() - wall_start
    metrics["total_wall_s"] = round(total_wall, 2)

    if args.workload > 0:
        _run_workload(args.workload, metrics)
    if args.slowest > 0:
        _run_slowest_tests(metrics, python_exe, n=args.slowest)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        print(f"Wrote {out_path}", file=sys.stderr)

    if not ok and metrics.get("total_wall_s", 0) < 15:
        metrics["hint"] = (
            "Pipeline failed quickly. Run from repo root with project env active "
            "(e.g. conda activate <your-env> or source .venv/bin/activate). "
            "Install deps first: make install-dev-full (or pip install -e packages/schemas -e apps/lean-gateway -e apps/orchestrator)."
        )

    print(json.dumps(metrics, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
