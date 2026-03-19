from __future__ import annotations

try:
    from langchain_core.tools import tool
except Exception:  # pragma: no cover

    def tool(func=None, **_kwargs):
        return func


from obligation_runtime_sdk.client import ObligationRuntimeClient

from .adapters import make_client


def build_toolset(base_url: str, client: ObligationRuntimeClient | None = None) -> list:
    """Build the Obligation Runtime LangChain toolset. Returns a list of tools in fixed order.

    Order: open_environment, create_session, apply_patch, check_interactive, get_goal, hover,
    definition, batch_verify, get_review_payload, submit_review_decision. Use by index or by
    binding to an agent; for named access, build a dict from the returned list (e.g. by tool name).
    """
    if client is None:
        client = make_client(base_url)

    @tool
    def open_environment_tool(
        repo_id: str,
        repo_path: str | None = None,
        repo_url: str | None = None,
        commit_sha: str = "HEAD",
    ) -> dict:
        """Open or reuse an environment snapshot for a repo."""
        return client.open_environment(
            repo_id=repo_id, repo_path=repo_path, repo_url=repo_url, commit_sha=commit_sha
        )

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
    def get_goal_tool(
        session_id: str, file_path: str, line: int, column: int, goal_kind: str = "plainGoal"
    ) -> dict:
        """Get goal at position in a file for an existing session."""
        return client.get_goal(
            session_id=session_id,
            file_path=file_path,
            line=line,
            column=column,
            goal_kind=goal_kind,
        )

    @tool
    def hover_tool(session_id: str, file_path: str, line: int, column: int) -> dict:
        """Get hover info at position in a file for an existing session."""
        return client.hover(session_id=session_id, file_path=file_path, line=line, column=column)

    @tool
    def definition_tool(session_id: str, file_path: str, line: int, column: int) -> dict:
        """Get definition location for symbol at position in a file for an existing session."""
        return client.definition(
            session_id=session_id, file_path=file_path, line=line, column=column
        )

    @tool
    def batch_verify_tool(
        session_id: str, target_files: list[str], target_declarations: list[str]
    ) -> dict:
        """Run authoritative batch verification for target files/declarations."""
        return client.batch_verify(
            session_id=session_id,
            target_files=target_files,
            target_declarations=target_declarations,
        )

    @tool
    def get_review_payload_tool(thread_id: str) -> dict:
        """Get review payload for a thread (when obligation is awaiting review)."""
        return client.get_review_payload(thread_id=thread_id)

    @tool
    def submit_review_decision_tool(thread_id: str, decision: str) -> dict:
        """Submit approve or reject for a thread. decision must be 'approve' or 'reject'."""
        return client.submit_review_decision(thread_id=thread_id, decision=decision)

    @tool
    def resume_tool(thread_id: str) -> dict:
        """Resume the graph after approve/reject. Requires checkpointer (e.g. Postgres) and OBR_ORCHESTRATOR_URL."""
        return client.resume(thread_id=thread_id)

    return [
        open_environment_tool,
        create_session_tool,
        apply_patch_tool,
        check_interactive_tool,
        get_goal_tool,
        hover_tool,
        definition_tool,
        batch_verify_tool,
        get_review_payload_tool,
        submit_review_decision_tool,
        resume_tool,
    ]
