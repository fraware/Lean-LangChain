from __future__ import annotations

try:
    from fastapi import FastAPI
except Exception:  # pragma: no cover
    class FastAPI:
        def __init__(self, **_kwargs): pass
        def include_router(self, *_args, **_kwargs): pass

from .routes_environment import router as environment_router
from .routes_sessions import router as session_router
from .routes_batch import router as batch_router


def create_app() -> FastAPI:
    app = FastAPI(title="Obligation Runtime Lean Gateway", version="0.1.0")
    app.include_router(environment_router, prefix="/v1")
    app.include_router(session_router, prefix="/v1")
    app.include_router(batch_router, prefix="/v1")
    return app


app = create_app()
