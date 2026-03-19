"""Typed stand-ins when FastAPI is not installed (import-time only)."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


class APIRouter:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def get(self, *args: Any, **kwargs: Any) -> Callable[[F], F]:
        def decorator(fn: F) -> F:
            return fn

        return decorator

    def post(self, *args: Any, **kwargs: Any) -> Callable[[F], F]:
        def decorator(fn: F) -> F:
            return fn

        return decorator


class HTTPException(Exception):
    def __init__(self, status_code: int = 500, detail: Any = None) -> None:
        super().__init__(str(detail))
        self.status_code = status_code
        self.detail = detail


class Request:
    pass


class BackgroundTasks:
    def add_task(self, *args: Any, **kwargs: Any) -> None:
        pass


class JSONResponse:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass


class Response:
    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        media_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        pass
