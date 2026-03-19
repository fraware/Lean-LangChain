from pathlib import Path

from lean_langchain_gateway.environment.fingerprint import FingerprintService
from lean_langchain_gateway.environment.snapshot_store import SnapshotStore


def test_snapshot_reuse(tmp_path: Path) -> None:
    repo = Path("tests/integration/fixtures/lean-mini")
    env = FingerprintService().build_from_repo(repo, repo_id="lean-mini", commit_sha="deadbeef")
    store = SnapshotStore(tmp_path)
    a = store.ensure_snapshot(env, repo)
    b = store.ensure_snapshot(env, repo)
    assert a.base_path == b.base_path
