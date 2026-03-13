"""API path constants shared by the Gateway and SDK. Single source of truth for v1 route paths."""

PREFIX = "/v1"

# Environment
PATH_ENVIRONMENTS_OPEN = "/environments/open"

# Sessions
PATH_SESSIONS = "/sessions"
PATH_SESSION_APPLY_PATCH = "/sessions/{session_id}/apply-patch"
PATH_SESSION_INTERACTIVE_CHECK = "/sessions/{session_id}/interactive-check"
PATH_SESSION_GOAL = "/sessions/{session_id}/goal"
PATH_SESSION_HOVER = "/sessions/{session_id}/hover"
PATH_SESSION_DEFINITION = "/sessions/{session_id}/definition"
PATH_SESSION_BATCH_VERIFY = "/sessions/{session_id}/batch-verify"

# Reviews
PATH_REVIEWS = "/reviews"
PATH_REVIEW_BY_THREAD = "/reviews/{thread_id}"
PATH_REVIEW_APPROVE = "/reviews/{thread_id}/approve"
PATH_REVIEW_REJECT = "/reviews/{thread_id}/reject"
PATH_REVIEW_RESUME = "/reviews/{thread_id}/resume"


def path_session(session_id: str, template: str) -> str:
    """Return full path for a session-scoped endpoint (e.g. apply-patch, batch-verify)."""
    return PREFIX + template.format(session_id=session_id)


def path_review(thread_id: str, template: str) -> str:
    """Return full path for a review-scoped endpoint (e.g. get payload, approve, resume)."""
    return PREFIX + template.format(thread_id=thread_id)
