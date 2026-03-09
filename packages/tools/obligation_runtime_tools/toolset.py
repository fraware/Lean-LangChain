from __future__ import annotations

try:
    from langchain_core.tools import tool
except Exception:  # pragma: no cover
    def tool(func=None, **_kwargs):
        return func

from .adapters import make_client


def build_toolset(base_url: str) -> list:
    client = make_client(base_url)

    @tool
    def open_environment_tool(repo_id: str, repo_path: str | None = None, repo_url: str | None = None, commit_sha: str = "HEAD") -> dict:
        """Open or reuse an environment snapshot for a repo."""
        return client.open_environment(repo_id=repo_id, repo_path=repo_path, repo_url=repo_url, commit_sha=commit_sha)

    @tool
    def create_session_tool(fingerprint_id: str) -> dict:
        """Create a session bound to an environment fingerprint."""
        return client.create_session(fingerprint_id=fingerprint_id)

    @tool
    def apply_patch_tool(session_id: str, files: dict[str, str]) -> dict:
        """Apply a file patch into the session overlay."""
        return client.apply_patch(session_id=session_id, files=files)

    @tool
    def check_interactive_tool(session_id: str, file_path: str) -> dict:
        """Run interactive Lean verification for a file in an existing session."""
        return client.interactive_check(session_id=session_id, file_path=file_path)

    @tool
    def batch_verify_tool(session_id: str, target_files: list[str], target_declarations: list[str]) -> dict:
        """Run authoritative batch verification for target files/declarations."""
        return client.batch_verify(session_id=session_id, target_files=target_files, target_declarations=target_declarations)

    return [
        open_environment_tool,
        create_session_tool,
        apply_patch_tool,
        check_interactive_tool,
        batch_verify_tool,
    ]
