from pathlib import Path

from lean_langchain_gateway.environment.fingerprint import FingerprintService


def test_same_repo_same_fingerprint() -> None:
    repo = Path("tests/integration/fixtures/lean-mini")
    service = FingerprintService()
    a = service.build_from_repo(repo, repo_id="lean-mini", commit_sha="deadbeef")
    b = service.build_from_repo(repo, repo_id="lean-mini", commit_sha="deadbeef")
    assert a.fingerprint_id() == b.fingerprint_id()
