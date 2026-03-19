from __future__ import annotations

try:
    from fastapi import APIRouter, HTTPException
except Exception:  # pragma: no cover
    from obligation_runtime_lean_gateway.api.fastapi_shim import (  # type: ignore[assignment]
        APIRouter,
        HTTPException,
    )

from obligation_runtime_schemas.api_paths import (
    PATH_SESSION_APPLY_PATCH,
    PATH_SESSION_DEFINITION,
    PATH_SESSION_GOAL,
    PATH_SESSION_HOVER,
    PATH_SESSION_INTERACTIVE_CHECK,
)
from obligation_runtime_schemas.gateway_api import (
    ApplyPatchRequest,
    ApplyPatchResponse,
    InteractiveCheckApiResponse,
    InteractiveCheckRequest,
    SessionDefinitionRequest,
    SessionDefinitionResponse,
    SessionGoalRequest,
    SessionGoalResponse,
    SessionHoverRequest,
    SessionHoverResponse,
)

from obligation_runtime_lean_gateway.api import deps
from obligation_runtime_lean_gateway.api.path_safety import resolve_under_root
from obligation_runtime_lean_gateway.server.transport import (
    transport_definition,
    transport_get_goal,
    transport_hover,
)

router = APIRouter()


@router.post(PATH_SESSION_APPLY_PATCH, response_model=ApplyPatchResponse)
def apply_patch(session_id: str, payload: ApplyPatchRequest) -> ApplyPatchResponse:
    try:
        lease = deps.session_manager.get(session_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail={"code": "session_not_found", "message": "Session not found"},
        )
    changed: list[str] = []
    for rel_path, content in payload.files.items():
        try:
            path = resolve_under_root(lease.workspace_path, rel_path)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail={"code": "path_traversal", "message": str(e)},
            ) from e
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        changed.append(rel_path)
    return ApplyPatchResponse(ok=True, session_id=session_id, changed_files=sorted(changed))


def _transport_supports_goal(transport: object) -> bool:
    return hasattr(transport, "get_goal") and callable(getattr(transport, "get_goal", None))


def _transport_supports_hover(transport: object) -> bool:
    return hasattr(transport, "hover") and callable(getattr(transport, "hover", None))


def _transport_supports_definition(transport: object) -> bool:
    return hasattr(transport, "definition") and callable(getattr(transport, "definition", None))


def _transport_supports_lsp(transport: object) -> bool:
    return _transport_supports_goal(transport)


@router.post(PATH_SESSION_INTERACTIVE_CHECK, response_model=InteractiveCheckApiResponse)
def interactive_check(
    session_id: str, payload: InteractiveCheckRequest
) -> InteractiveCheckApiResponse:
    try:
        deps.session_manager.get(session_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail={"code": "session_not_found", "message": "Session not found"},
        )
    result = deps.interactive_api.check_interactive(
        session_id=session_id, file_path=payload.file_path
    )
    lsp_required = not _transport_supports_lsp(deps.interactive_api.transport)
    data = result.model_dump(mode="json")
    data["lsp_required"] = lsp_required
    return InteractiveCheckApiResponse.model_validate(data)


@router.post(PATH_SESSION_GOAL, response_model=SessionGoalResponse)
def goal(session_id: str, payload: SessionGoalRequest) -> SessionGoalResponse:
    try:
        deps.session_manager.get(session_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail={"code": "session_not_found", "message": "Session not found"},
        )
    transport = deps.interactive_api.transport
    goals = transport_get_goal(
        transport,
        session_id,
        payload.file_path,
        payload.line,
        payload.column,
        payload.goal_kind,
    )
    return SessionGoalResponse(
        ok=True,
        goal_kind=payload.goal_kind,
        goals=goals,
        line=payload.line,
        column=payload.column,
        lsp_required=not _transport_supports_goal(transport),
    )


@router.post(PATH_SESSION_HOVER, response_model=SessionHoverResponse)
def hover(session_id: str, payload: SessionHoverRequest) -> SessionHoverResponse:
    try:
        deps.session_manager.get(session_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail={"code": "session_not_found", "message": "Session not found"},
        )
    transport = deps.interactive_api.transport
    contents = transport_hover(
        transport,
        session_id,
        payload.file_path,
        payload.line,
        payload.column,
    )
    return SessionHoverResponse(
        ok=True,
        contents=contents,
        file_path=payload.file_path,
        line=payload.line,
        column=payload.column,
        lsp_required=not _transport_supports_hover(transport),
    )


@router.post(PATH_SESSION_DEFINITION, response_model=SessionDefinitionResponse)
def definition(session_id: str, payload: SessionDefinitionRequest) -> SessionDefinitionResponse:
    try:
        deps.session_manager.get(session_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail={"code": "session_not_found", "message": "Session not found"},
        )
    transport = deps.interactive_api.transport
    locations = transport_definition(
        transport,
        session_id,
        payload.file_path,
        payload.line,
        payload.column,
    )
    return SessionDefinitionResponse(
        ok=True,
        locations=locations,
        file_path=payload.file_path,
        line=payload.line,
        column=payload.column,
        lsp_required=not _transport_supports_definition(transport),
    )
