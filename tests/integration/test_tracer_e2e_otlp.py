"""E2E test: emit a span via OtlpTracer and assert it is received by an in-memory exporter.

Requires obligation-runtime-telemetry[otlp]. Run with the telemetry-e2e CI job or:
  pip install obligation-runtime-telemetry[otlp] && pytest tests/integration/test_tracer_e2e_otlp.py -v
"""

from __future__ import annotations

import pytest

from obligation_runtime_telemetry.events import RuntimeNodeEvent
from obligation_runtime_telemetry.tracer import get_production_tracer


def test_tracer_e2e_emitted_span_received_by_in_memory_exporter() -> None:
    """E2E: TracerProvider + InMemorySpanExporter; get_production_tracer(provider); emit; assert span received."""
    pytest.importorskip(
        "opentelemetry.sdk.trace", reason="install obligation-runtime-telemetry[otlp]"
    )
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    try:
        from opentelemetry.sdk.trace.export import InMemorySpanExporter
    except ImportError:
        from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
            InMemorySpanExporter,
        )

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    tracer = get_production_tracer(provider=provider)
    assert tracer is not None

    event = RuntimeNodeEvent(
        event_type="node_exit",
        span_name="obr.e2e_test",
        thread_id="e2e-thread",
        obligation_id="e2e-obl",
        node_name="batch_verify",
        status="ok",
        timing_ms=42,
    )
    tracer.emit(event)

    finished = exporter.get_finished_spans()
    assert len(finished) >= 1
    span = finished[0]
    assert span.name == "obr.e2e_test"
    assert dict(span.attributes).get("thread_id") == "e2e-thread"
    assert dict(span.attributes).get("node_name") == "batch_verify"
    assert dict(span.attributes).get("timing_ms") == 42
