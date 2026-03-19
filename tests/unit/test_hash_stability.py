from lean_langchain_schemas.environment import EnvironmentFingerprint
from lean_langchain_schemas.hashing import canonical_sha256


def test_hash_stability_for_dict_order() -> None:
    a = {"b": 2, "a": 1}
    b = {"a": 1, "b": 2}
    assert canonical_sha256(a) == canonical_sha256(b)


def test_fingerprint_id_deterministic() -> None:
    """Same EnvironmentFingerprint payload yields same fingerprint_id twice."""
    env = EnvironmentFingerprint(
        repo_id="repo1",
        repo_url="https://example.com/repo.git",
        commit_sha="abc123",
        lean_toolchain="leanprover/lean4:4.28.0",
        lakefile_hash="lakehash",
        manifest_hash="manihash",
    )
    a = env.fingerprint_id()
    b = env.fingerprint_id()
    assert a == b
    assert len(a) == 64
    assert all(c in "0123456789abcdef" for c in a)
