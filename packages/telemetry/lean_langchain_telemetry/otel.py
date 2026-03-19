"""OpenTelemetry helpers: configure OTLP from env for runtime tracing."""

from __future__ import annotations

import os
from typing import Any


def get_otlp_endpoint() -> str | None:
    """Return OTLP endpoint from OBR_OTLP_ENDPOINT or OTEL_EXPORTER_OTLP_ENDPOINT, or None."""
    return (
        os.environ.get("OBR_OTLP_ENDPOINT") or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") or None
    )


def configure_otel() -> Any:
    """Configure OTLP tracer from env; return tracer or None if endpoint unset or opentelemetry missing."""
    from lean_langchain_telemetry.tracer import _make_otlp_tracer

    return _make_otlp_tracer()
