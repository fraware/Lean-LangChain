from __future__ import annotations

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
except Exception:  # pragma: no cover — fallback when FastAPI not installed (e.g. schema-only tests)
    class FastAPI:
        def __init__(self, **_kwargs): pass
        def include_router(self, *_args, **_kwargs): pass
        def add_middleware(self, *_args, **_kwargs): pass
    class HTTPException(Exception): ...
    class Request: ...
    def JSONResponse(*_args, **_kwargs): ...
    class CORSMiddleware:
        pass

from .routes_environment import router as environment_router
from .routes_sessions import router as session_router
from .routes_batch import router as batch_router
from .routes_reviews import router as review_router
from .routes_health import router as health_router
from . import routes_metrics as _routes_metrics
from .errors import (
    NOT_FOUND,
    VALIDATION_ERROR,
    PATH_TRAVERSAL,
    INTERNAL_ERROR,
    error_envelope,
    _detail_code_and_message,
    redact_secrets,
)
from .logging_config import configure_logging, request_id_ctx


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or "req_local"


def _cors_origins() -> list[str]:
    raw = os.environ.get("OBR_CORS_ORIGINS", "")
    return [o.strip() for o in raw.split(",") if o.strip()]


def _assert_production_state() -> None:
    """When OBR_ENV=production, require Postgres, real axiom audit, and (when strict) real fresh checker."""
    if os.environ.get("OBR_ENV") != "production":
        return
    review_store = os.environ.get("REVIEW_STORE", "memory")
    checkpointer = os.environ.get("CHECKPOINTER", "memory")
    database_url = os.environ.get("DATABASE_URL", "").strip()
    strict = os.environ.get("OBR_ACCEPTANCE_STRICT", "1").strip().lower() in ("1", "true", "yes")
    errors = []
    if review_store == "memory":
        errors.append("REVIEW_STORE must not be memory when OBR_ENV=production")
    if checkpointer == "memory":
        errors.append("CHECKPOINTER must not be memory when OBR_ENV=production")
    if not database_url:
        errors.append("DATABASE_URL must be set when OBR_ENV=production")
    if not os.environ.get("OBR_USE_REAL_AXIOM_AUDIT"):
        errors.append(
            "OBR_USE_REAL_AXIOM_AUDIT must be set when OBR_ENV=production (real axiom audit required)"
        )
    if strict and not os.environ.get("OBR_USE_REAL_FRESH_CHECKER"):
        errors.append(
            "OBR_USE_REAL_FRESH_CHECKER must be set when OBR_ENV=production and OBR_ACCEPTANCE_STRICT"
        )
    if errors:
        raise RuntimeError("; ".join(errors))


class _SecretRedactionFilter(logging.Filter):
    """Redact secret values in log records before they are emitted."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_secrets(record.msg)
        if record.args:
            record.args = tuple(
                redact_secrets(str(a)) if isinstance(a, str) else a for a in record.args
            )
        return True


def _warn_production_tracer_if_unset() -> None:
    """When OBR_ENV=production and no tracer backend is configured, log a warning."""
    if os.environ.get("OBR_ENV") != "production":
        return
    try:
        from obligation_runtime_telemetry.tracer import get_production_tracer
        if get_production_tracer() is None:
            logging.getLogger(__name__).warning(
                "OBR_ENV=production but no tracer configured: set OBR_OTLP_ENDPOINT or LANGCHAIN_API_KEY for observability"
            )
    except ImportError:
        pass


@asynccontextmanager
async def _lifespan(app: FastAPI):
    _assert_production_state()
    configure_logging()
    for handler in logging.root.handlers:
        handler.addFilter(_SecretRedactionFilter())
    _warn_production_tracer_if_unset()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Obligation Runtime Lean Gateway",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=_lifespan,
    )

    origins = _cors_origins()
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(health_router)
    if os.environ.get("OBR_METRICS_ENABLED") and hasattr(_routes_metrics, "record_request") and _routes_metrics.REQUEST_COUNT is not None:
        app.include_router(_routes_metrics.router)

        @app.middleware("http")
        async def metrics_middleware(request: Request, call_next):
            start = time.perf_counter()
            response = await call_next(request)
            _routes_metrics.record_request(
                request.method,
                request.url.path,
                response.status_code,
                time.perf_counter() - start,
            )
            return response

    app.include_router(environment_router, prefix="/v1")
    app.include_router(session_router, prefix="/v1")
    app.include_router(batch_router, prefix="/v1")
    app.include_router(review_router, prefix="/v1")

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_ctx.set(request.state.request_id)
        try:
            return await call_next(request)
        finally:
            request_id_ctx.reset(token)

    @app.exception_handler(HTTPException)
    def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        code, message = _detail_code_and_message(exc.detail)
        body = error_envelope(code=code, message=message, request_id=_request_id(request))
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(Exception)
    def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, (FileNotFoundError, LookupError, KeyError)):
            code, status = NOT_FOUND, 404
        elif isinstance(exc, ValueError):
            code = PATH_TRAVERSAL if "escapes" in str(exc).lower() else VALIDATION_ERROR
            status = 400
        else:
            code, status = INTERNAL_ERROR, 500
        message = redact_secrets(str(exc))
        body = error_envelope(code=code, message=message, request_id=_request_id(request))
        return JSONResponse(status_code=status, content=body)

    return app


app = create_app()
