# Obligation Runtime Telemetry

**Purpose:** In-process tracer, OTLP and LangSmith tracers, and LangSmith dataset/experiment helpers. **Audience:** contributors and operators.

## Default: in-process tracer

The default path uses `InMemoryTracer`: the graph (or runtime) emits events via `tracer.emit(event)`, and events are stored in memory. This is used in tests and when no external observability is configured. Events are `RuntimeNodeEvent` (or dicts that validate to it) with `event_type`, `span_name`, `thread_id`, `obligation_id`, `node_name`, `status`, `timestamp`, `timing_ms`, `failure_class`, `metadata`.

## Production: OTLP or LangSmith

`get_production_tracer()` returns a tracer when configured, else `None`:

- **OTLP:** Set `OBR_OTLP_ENDPOINT` or `OTEL_EXPORTER_OTLP_ENDPOINT` (e.g. `http://localhost:4317`). Install optional deps: `pip install obligation-runtime-telemetry[otlp]`. `OtlpTracer` converts each event to an OpenTelemetry span and exports via OTLP (gRPC).
- **LangSmith:** Set `LANGCHAIN_API_KEY` or `LANGCHAIN_TRACING_V2`. Install optional: `pip install obligation-runtime-telemetry[langsmith]`. `LangSmithTracer` sends run-like data to LangSmith.

No hard dependency on `opentelemetry-*` or `langsmith` in the default install. The runtime and graph accept an optional `tracer` argument; pass `InMemoryTracer()` for tests or `get_production_tracer()` for production when configured.

## LangSmith datasets and experiments

`packages/telemetry/obligation_runtime_telemetry/langsmith.py` provides helpers for fixed-corpus experiments: `create_dataset`, `run_experiment`, and `patch_admissibility_runnable_factory`. The factory returns a runnable that takes example inputs (e.g. obligation_input with events and obligation_class), runs the protocol evaluator, and returns decision/trust_level/reasons; use with `run_on_dataset` for "experiments run on a fixed corpus." When the LangSmith SDK is missing or auth fails (e.g. 401 or invalid token), helpers return `status: "error"` with a message; callers must handle errors. With a valid key, helpers return `created`, `run`, `compare`, or `promoted` as appropriate. Tests: `tests/unit/test_langsmith.py`, `tests/integration/test_langsmith_fixed_corpus.py`. Optional CI job **langsmith** runs when `LANGCHAIN_API_KEY` is set. Local: `make test-langsmith`.

### Evaluator comparison and trace promotion

- **compare_runs(run_ids):** Compares two or more LangSmith runs (e.g. evaluator runs or experiment runs). Fetches each run via `read_run`, returns a structured dict with `runs` (inputs, outputs, error, latency_ms per run) and a `summary`. Use to compare A/B runs or before/after evaluator outputs. Returns `status: "error"` with a message when the SDK is missing or auth fails.

- **trace_to_dataset(trace_ids, dataset_name):** Promotes selected traces (run IDs) to a LangSmith dataset. Resolves or creates the dataset by name, then for each trace ID calls `read_run` and `create_example_from_run` so the trace becomes a dataset example. Use to build a dataset from production or experiment traces for later evaluation. Returns dataset_id, promoted_count, and run_ids; returns `status: "error"` when SDK is missing or auth fails.

**See also:** [docs/architecture/telemetry-and-evals.md](../../../docs/architecture/telemetry-and-evals.md), [docs/workflow.md](../../../docs/workflow.md), [../../README.md](../README.md).
