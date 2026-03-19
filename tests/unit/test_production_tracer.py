"""Unit tests for production tracers: get_production_tracer, OtlpTracer.emit, LangSmithTracer.emit.

Validates that get_production_tracer() returns the correct tracer (or None) based on
OBR_OTLP_ENDPOINT / LANGCHAIN_API_KEY and optional dependency availability; that
OtlpTracer and LangSmithTracer correctly map RuntimeNodeEvent to spans/runs and
call start_span/end or the LangSmith client. Used in CI without real OTLP or
LangSmith endpoints. See docs/workflow.md (LangSmith/telemetry)
and docs/architecture/telemetry-and-evals.md.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

from lean_langchain_telemetry.events import RuntimeNodeEvent
from lean_langchain_telemetry.tracer import (
    LangSmithTracer,
    OtlpTracer,
    get_production_tracer,
)


def test_get_production_tracer_returns_none_with_no_env() -> None:
    """With no OTLP or LangSmith env vars, get_production_tracer returns None."""
    keys = (
        "OBR_OTLP_ENDPOINT",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "LANGCHAIN_API_KEY",
        "LANGCHAIN_TRACING_V2",
    )
    saved = {k: os.environ.pop(k, None) for k in keys if k in os.environ}
    try:
        result = get_production_tracer()
        assert result is None
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v


def test_get_production_tracer_otlp_env_but_no_deps_returns_none_or_otlp() -> None:
    """With OBR_OTLP_ENDPOINT set (and no LangSmith), returns OtlpTracer if deps present else None."""
    env = {"OBR_OTLP_ENDPOINT": "http://localhost:4317"}
    # Unset LangSmith keys so we only test the OTLP branch (avoids returning LangSmithTracer when .env has LANGCHAIN_API_KEY)
    for k in ("LANGCHAIN_API_KEY", "LANGCHAIN_TRACING_V2"):
        env[k] = ""
    with patch.dict(os.environ, env, clear=False):
        with patch("lean_langchain_telemetry.tracer._make_otlp_tracer", return_value=None):
            result = get_production_tracer()
    assert result is None


def test_get_production_tracer_langsmith_env_but_no_deps_returns_none() -> None:
    """With LANGCHAIN_API_KEY set but langsmith not installed, returns None."""
    with patch.dict(os.environ, {"LANGCHAIN_API_KEY": "test-key"}, clear=False):
        with patch("lean_langchain_telemetry.tracer._langsmith_client", return_value=None):
            result = get_production_tracer()
    assert result is None


def test_otlp_tracer_emit_with_mock_tracer_calls_start_span_and_end() -> None:
    """OtlpTracer.emit starts a span, sets attributes, and ends it when _tracer is set."""
    mock_span = MagicMock()
    mock_tracer = MagicMock()
    mock_tracer.start_span.return_value = mock_span

    with patch("lean_langchain_telemetry.tracer._make_otlp_tracer", return_value=mock_tracer):
        otlp = OtlpTracer()
    event = RuntimeNodeEvent(
        event_type="node_exit",
        span_name="obr.test",
        thread_id="t1",
        obligation_id="o1",
        node_name="test_node",
        status="ok",
        timing_ms=10,
    )
    otlp.emit(event)
    mock_tracer.start_span.assert_called_once()
    assert mock_tracer.start_span.call_args[0][0] == "obr.test"
    mock_span.set_attribute.assert_called()
    mock_span.set_status.assert_called_once()
    mock_span.end.assert_called_once()


def test_otlp_tracer_emit_with_none_tracer_does_not_raise() -> None:
    """OtlpTracer.emit does nothing when _tracer is None (no opentelemetry)."""
    with patch("lean_langchain_telemetry.tracer._make_otlp_tracer", return_value=None):
        otlp = OtlpTracer()
    event = RuntimeNodeEvent(
        event_type="node_enter",
        span_name="obr.init",
        thread_id="t1",
        obligation_id="o1",
        node_name="init",
        status="running",
    )
    otlp.emit(event)


def test_langsmith_tracer_emit_with_mock_client_calls_create_run() -> None:
    """LangSmithTracer.emit calls client.create_run with expected inputs when _client is set."""
    mock_client = MagicMock()
    with patch("lean_langchain_telemetry.tracer._langsmith_client", return_value=mock_client):
        ls = LangSmithTracer()
    event = RuntimeNodeEvent(
        event_type="node_exit",
        span_name="obr.batch",
        thread_id="t1",
        obligation_id="o1",
        node_name="batch_verify",
        status="ok",
        timing_ms=100,
    )
    ls.emit(event)
    mock_client.create_run.assert_called_once()
    call_kw = mock_client.create_run.call_args[1]
    assert call_kw["name"] == "obr.batch"
    assert call_kw["run_type"] == "chain"
    assert call_kw["inputs"]["thread_id"] == "t1"
    assert call_kw["inputs"]["node"] == "batch_verify"
    assert call_kw["extra"]["status"] == "ok"
    assert call_kw["extra"]["timing_ms"] == 100


def test_langsmith_tracer_emit_with_none_client_does_not_raise() -> None:
    """LangSmithTracer.emit does nothing when _client is None."""
    with patch("lean_langchain_telemetry.tracer._langsmith_client", return_value=None):
        ls = LangSmithTracer()
    event = RuntimeNodeEvent(
        event_type="node_enter",
        span_name="obr.init",
        thread_id="t1",
        obligation_id="o1",
        node_name="init",
        status="running",
    )
    ls.emit(event)


def test_get_production_tracer_returns_otlp_when_mock_tracer_injected() -> None:
    """When OTLP env set and _make_otlp_tracer returns a tracer, get_production_tracer returns OtlpTracer."""
    mock_tracer = MagicMock()
    with patch.dict(os.environ, {"OBR_OTLP_ENDPOINT": "http://localhost:4317"}, clear=False):
        with patch(
            "lean_langchain_telemetry.tracer._make_otlp_tracer", return_value=mock_tracer
        ):
            result = get_production_tracer()
    assert result is not None
    assert isinstance(result, OtlpTracer)


def test_get_production_tracer_returns_langsmith_when_mock_client_injected() -> None:
    """When LANGCHAIN_API_KEY set and _langsmith_client returns client, get_production_tracer returns LangSmithTracer."""
    mock_client = MagicMock()
    with patch.dict(os.environ, {"LANGCHAIN_API_KEY": "key"}, clear=False):
        with patch(
            "lean_langchain_telemetry.tracer._langsmith_client", return_value=mock_client
        ):
            result = get_production_tracer()
    assert result is not None
    assert isinstance(result, LangSmithTracer)


def test_production_tracer_with_env_emits_to_mock_exporter() -> None:
    """With OBR_OTLP_ENDPOINT set and mock tracer, get_production_tracer().emit() invokes span start/end (CI proof)."""
    mock_span = MagicMock()
    mock_tracer = MagicMock()
    mock_tracer.start_span.return_value = mock_span
    with patch.dict(os.environ, {"OBR_OTLP_ENDPOINT": "http://test:4317"}, clear=False):
        with patch(
            "lean_langchain_telemetry.tracer._make_otlp_tracer", return_value=mock_tracer
        ):
            tracer = get_production_tracer()
    assert tracer is not None
    event = RuntimeNodeEvent(
        event_type="node_exit",
        span_name="obr.ci_test",
        thread_id="t1",
        obligation_id="o1",
        node_name="test_node",
        status="ok",
        timing_ms=5,
    )
    tracer.emit(event)
    mock_tracer.start_span.assert_called_once()
    mock_span.end.assert_called_once()


def test_otlp_tracer_emit_propagates_event_fields_to_span_attributes() -> None:
    """OtlpTracer.emit sets span attributes from event (thread_id, node_name, etc)."""
    mock_span = MagicMock()
    mock_tracer = MagicMock()
    mock_tracer.start_span.return_value = mock_span

    with patch(
        "lean_langchain_telemetry.tracer._make_otlp_tracer",
        return_value=mock_tracer,
    ):
        otlp = OtlpTracer()
    event = RuntimeNodeEvent(
        event_type="node_exit",
        span_name="obr.attrs",
        thread_id="thread-xyz",
        obligation_id="obl-1",
        node_name="batch_verify",
        status="ok",
        timing_ms=250,
    )
    otlp.emit(event)

    calls = {c[0][0]: c[0][1] for c in mock_span.set_attribute.call_args_list}
    assert calls.get("thread_id") == "thread-xyz"
    assert calls.get("obligation_id") == "obl-1"
    assert calls.get("node_name") == "batch_verify"
    assert calls.get("status") == "ok"
    assert calls.get("timing_ms") == 250


def test_langsmith_tracer_multiple_emit_calls_create_multiple_runs() -> None:
    """LangSmithTracer.emit twice results in two create_run calls."""
    mock_client = MagicMock()
    with patch(
        "lean_langchain_telemetry.tracer._langsmith_client",
        return_value=mock_client,
    ):
        ls = LangSmithTracer()
    for i in range(2):
        ls.emit(
            RuntimeNodeEvent(
                event_type="node_exit",
                span_name=f"obr.run_{i}",
                thread_id="t1",
                obligation_id="o1",
                node_name="node",
                status="ok",
                timing_ms=10 * (i + 1),
            )
        )
    assert mock_client.create_run.call_count == 2
    assert mock_client.create_run.call_args_list[0][1]["name"] == "obr.run_0"
    assert mock_client.create_run.call_args_list[1][1]["name"] == "obr.run_1"
