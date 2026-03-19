from pathlib import Path

from lean_langchain_gateway.environment.fingerprint import FingerprintService
from lean_langchain_gateway.environment.overlay_fs import OverlayFS
from lean_langchain_gateway.environment.snapshot_store import SnapshotStore


def test_overlay_does_not_mutate_base(tmp_path: Path) -> None:
    repo = Path("tests/integration/fixtures/lean-mini")
    env = FingerprintService().build_from_repo(repo, repo_id="lean-mini", commit_sha="deadbeef")
    snapshot = SnapshotStore(tmp_path).ensure_snapshot(env, repo)
    overlay = OverlayFS(tmp_path).create_overlay(snapshot)

    overlay_file = overlay.overlay_path / "Mini/Basic.lean"
    base_file = snapshot.base_path / "Mini/Basic.lean"

    original = base_file.read_text(encoding="utf-8")
    overlay_file.write_text(original + "\n-- changed\n", encoding="utf-8")

    assert base_file.read_text(encoding="utf-8") == original
