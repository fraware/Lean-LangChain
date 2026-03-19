"""Prometheus /metrics endpoint (optional: install with [metrics] extra, set OBR_METRICS_ENABLED=1)."""

from __future__ import annotations

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
except ImportError:
    Counter = None
    Histogram = None
    generate_latest = None
    CONTENT_TYPE_LATEST = "text/plain"

try:
    from fastapi import APIRouter
    from fastapi.responses import Response
except Exception:  # pragma: no cover
    from lean_langchain_gateway.api.fastapi_shim import (  # type: ignore[assignment]
        APIRouter,
        Response,
    )


router = APIRouter(tags=["metrics"])

REQUEST_COUNT = (
    Counter(
        "obr_http_requests_total",
        "Total HTTP requests",
        ["method", "path", "status_class"],
    )
    if Counter
    else None
)

REQUEST_LATENCY = (
    Histogram(
        "obr_http_request_duration_seconds",
        "HTTP request latency in seconds",
        ["method", "path"],
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    )
    if Histogram
    else None
)


def _status_class(status_code: int) -> str:
    if status_code < 400:
        return "2xx"
    if status_code < 500:
        return "4xx"
    return "5xx"


@router.get("/metrics")
def metrics() -> Response:
    """Prometheus text format; only registered when OBR_METRICS_ENABLED=1 and prometheus_client installed."""
    if generate_latest is None:
        return Response(content="", status_code=404)
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


def record_request(method: str, path: str, status_code: int, duration_seconds: float) -> None:
    """Call from middleware to record a request (no-op if metrics not enabled)."""
    if REQUEST_COUNT is not None:
        REQUEST_COUNT.labels(
            method=method, path=path, status_class=_status_class(status_code)
        ).inc()
    if REQUEST_LATENCY is not None:
        REQUEST_LATENCY.labels(method=method, path=path).observe(duration_seconds)
