from obligation_runtime_schemas.environment import EnvironmentFingerprint


def test_environment_roundtrip() -> None:
    env = EnvironmentFingerprint(
        repo_id="repo1",
        repo_url="https://example.com/repo.git",
        commit_sha="abc123",
        lean_toolchain="leanprover/lean4:4.28.0",
        lakefile_hash="lakehash",
        manifest_hash="manihash",
    )
    raw = env.model_dump(mode="json")
    restored = EnvironmentFingerprint.model_validate(raw)
    assert restored == env
