# Telemetry and evals

Tracing (OTLP, LangSmith), datasets, experiments, and how CI tests them. For workflow and LangSmith/LangGraph integration, see [workflow.md](../workflow.md).

## Production tracer

- The runtime can emit telemetry via an optional tracer (`get_production_tracer()`). When configured (OTLP endpoint or LangSmith), events become spans or LangSmith runs. When not configured, the default is `InMemoryTracer` (in-process only).
- **CI:** The main CI job runs `tests/unit/test_production_tracer.py`, which uses mocks (mock OTLP tracer, mock LangSmith client) to validate the tracer path and `emit()` behavior. No real OTLP or LangSmith endpoint is used in CI. For local E2E with a real endpoint, set `OBR_OTLP_ENDPOINT` (or `OTEL_EXPORTER_OTLP_ENDPOINT`) and run a flow that emits spans; verify receipt in your collector. See [tests-and-ci.md](../tests-and-ci.md) and `packages/telemetry/lean_langchain_telemetry/README.md`.

## LangSmith

- **Datasets and experiments:** `create_dataset`, `run_experiment`, and `patch_admissibility_runnable_factory` support fixed-corpus experiments; the optional **langsmith** CI job runs when `LANGCHAIN_API_KEY` is set. See `packages/telemetry/lean_langchain_telemetry/README.md`.
- **Evaluator comparison:** `compare_runs(run_ids)` fetches two or more LangSmith runs via `read_run` and returns a structured comparison (inputs, outputs, error, latency_ms per run, plus summary). Use for A/B or evaluator run comparison.
- **Trace-to-dataset promotion:** `trace_to_dataset(trace_ids, dataset_name)` promotes selected run IDs to a LangSmith dataset (creates or resolves the dataset, then `create_example_from_run` for each trace). Use to build a dataset from production or experiment traces for later evaluation.

## Regression and golden cases

Regression tests and golden outputs are covered in the test suite and runbooks; see `docs/runbooks/evaluation.md` and `docs/demos/README.md`.

**See also:** [workflow.md](../workflow.md), [tests-and-ci.md](../tests-and-ci.md), [runbooks/evaluation.md](../runbooks/evaluation.md), [packages/telemetry/lean_langchain_telemetry/README.md](../../packages/telemetry/lean_langchain_telemetry/README.md).
