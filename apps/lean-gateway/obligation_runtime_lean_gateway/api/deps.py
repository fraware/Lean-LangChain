from __future__ import annotations

from pathlib import Path

from obligation_runtime_lean_gateway.environment.fingerprint import FingerprintService
from obligation_runtime_lean_gateway.environment.snapshot_store import SnapshotStore
from obligation_runtime_lean_gateway.environment.overlay_fs import OverlayFS
from obligation_runtime_lean_gateway.server.session_manager import SessionManager
from obligation_runtime_lean_gateway.server.worker_pool import WorkerPool
from obligation_runtime_lean_gateway.server.interactive_api import InteractiveAPI
from obligation_runtime_lean_gateway.batch.build_runner import BuildRunner
from obligation_runtime_lean_gateway.batch.axiom_audit import AxiomAuditor
from obligation_runtime_lean_gateway.batch.fresh_checker import FreshChecker


_DATA_ROOT = Path('.var')

fingerprints = FingerprintService()
snapshots = SnapshotStore(_DATA_ROOT)
overlays = OverlayFS(_DATA_ROOT)
session_manager = SessionManager()
worker_pool = WorkerPool()
interactive_api = InteractiveAPI(session_manager, worker_pool)
build_runner = BuildRunner()
axiom_auditor = AxiomAuditor()
fresh_checker = FreshChecker()
