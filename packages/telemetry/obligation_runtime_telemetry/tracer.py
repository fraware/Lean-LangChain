"""Tracers for runtime node events. Default: InMemoryTracer. Production: OTLP/LangSmith. See README.md."""

from __future__ import annotations

import os
from typing import Any

from .events import RuntimeNodeEvent


class InMemoryTracer:
    def __init__(self) -> None:
        self.events: list[RuntimeNodeEvent] = []

    def emit(self, event: RuntimeNodeEvent | dict) -> None:
        if isinstance(event, dict):
            event = RuntimeNodeEvent.model_validate(event)
        self.events.append(event)


class OtlpTracer:
    """Export runtime events as OpenTelemetry spans via OTLP. Requires opentelemetry-* (optional dep)."""

    def __init__(self, tracer: Any = None) -> None:
        """Optional tracer for testing (e.g. from a TracerProvider with InMemorySpanExporter)."""
        self._tracer = tracer if tracer is not None else _make_otlp_tracer()

    def emit(self, event: RuntimeNodeEvent | dict) -> None:
        if isinstance(event, dict):
            event = RuntimeNodeEvent.model_validate(event)
        if self._tracer is None:
            return
        span = self._tracer.start_span(event.span_name or event.node_name)
        try:
            span.set_attribute("thread_id", event.thread_id)
            span.set_attribute("obligation_id", event.obligation_id)
            span.set_attribute("node_name", event.node_name)
            span.set_attribute("status", event.status)
            if event.timing_ms is not None:
                span.set_attribute("timing_ms", event.timing_ms)
            if event.failure_class:
                span.set_attribute("failure_class", event.failure_class)
            span.set_status(_otel_status_ok() if event.status == "ok" else _otel_status_error())
        finally:
            span.end()


def _make_otlp_tracer():
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider()
        endpoint = os.environ.get("OBR_OTLP_ENDPOINT") or os.environ.get(
            "OTEL_EXPORTER_OTLP_ENDPOINT"
        )
        if not endpoint:
            return None
        exporter = OTLPSpanExporter(endpoint=endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        return trace.get_tracer("obligation-runtime", "0.1.0")
    except ImportError:
        return None


def _otel_status_ok():
    try:
        from opentelemetry.trace import Status, StatusCode

        return Status(StatusCode.OK)
    except ImportError:
        return None


def _otel_status_error():
    try:
        from opentelemetry.trace import Status, StatusCode

        return Status(StatusCode.ERROR)
    except ImportError:
        return None


class LangSmithTracer:
    """Send span-like data to LangSmith when SDK and API key are configured."""

    def __init__(self) -> None:
        self._client = _langsmith_client()

    def emit(self, event: RuntimeNodeEvent | dict) -> None:
        if isinstance(event, dict):
            event = RuntimeNodeEvent.model_validate(event)
        if self._client is None:
            return
        try:
            self._client.create_run(
                name=event.span_name or event.node_name,
                run_type="chain",
                inputs={"thread_id": event.thread_id, "node": event.node_name},
                extra={"status": event.status, "timing_ms": event.timing_ms},
            )
        except Exception:
            pass


def _langsmith_client():
    if not os.environ.get("LANGCHAIN_API_KEY") and not os.environ.get("LANGCHAIN_TRACING_V2"):
        return None
    try:
        from langsmith import Client

        return Client()
    except ImportError:
        return None


def get_production_tracer(provider: Any = None):
    """Return OtlpTracer when OTLP endpoint or provider given, else LangSmithTracer when API key set, else None.

    For E2E tests, pass a TracerProvider configured with InMemorySpanExporter to assert spans.
    """
    if provider is not None:
        try:
            tracer = provider.get_tracer("obligation-runtime", "0.1.0")
            return OtlpTracer(tracer=tracer)
        except Exception:
            pass
    if os.environ.get("OBR_OTLP_ENDPOINT") or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        t = OtlpTracer()
        if t._tracer is not None:
            return t
    if os.environ.get("LANGCHAIN_API_KEY") or os.environ.get("LANGCHAIN_TRACING_V2"):
        t = LangSmithTracer()
        if t._client is not None:
            return t
    return None
