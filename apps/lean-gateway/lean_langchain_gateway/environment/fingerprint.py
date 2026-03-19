from __future__ import annotations

import hashlib
from pathlib import Path

from lean_langchain_schemas.environment import EnvironmentFingerprint


class FingerprintService:
    def hash_file(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def build_from_repo(
        self, repo_root: Path, repo_id: str, commit_sha: str, repo_url: str | None = None
    ) -> EnvironmentFingerprint:
        toolchain_path = repo_root / "lean-toolchain"
        lake_toml = repo_root / "lakefile.toml"
        lake_lean = repo_root / "lakefile.lean"
        manifest = repo_root / "lake-manifest.json"

        if not toolchain_path.exists():
            raise FileNotFoundError("lean-toolchain not found")

        lakefile_path = lake_toml if lake_toml.exists() else lake_lean
        if not lakefile_path.exists():
            raise FileNotFoundError("lakefile.toml or lakefile.lean not found")

        lean_toolchain = toolchain_path.read_text(encoding="utf-8").strip()
        lakefile_hash = self.hash_file(lakefile_path)
        manifest_hash = self.hash_file(manifest) if manifest.exists() else None

        return EnvironmentFingerprint(
            repo_id=repo_id,
            repo_url=repo_url,
            commit_sha=commit_sha,
            lean_toolchain=lean_toolchain,
            lakefile_hash=lakefile_hash,
            manifest_hash=manifest_hash,
        )
