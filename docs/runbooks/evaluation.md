# Evaluation runbook

How to run LangSmith experiments and the regression corpus.

## LangSmith experiments

1. **Before you start:** Install `langsmith` and set `LANGCHAIN_API_KEY` (or `LANGSMITH_API_KEY`). See [workflow.md](../workflow.md) (LangSmith integration).

2. **Create a dataset:** Use telemetry helpers or LangSmith UI.
   - From code: `from obligation_runtime_telemetry.langsmith import create_dataset` then `create_dataset(name, description=..., examples=[...])`. Returns `{"status": "created", "dataset_id": ...}` or `{"status": "error", "message": ...}` if SDK/auth missing.

3. **Run an experiment:** `from obligation_runtime_telemetry.langsmith import run_experiment, patch_admissibility_runnable_factory` then `run_experiment(dataset_name, patch_admissibility_runnable_factory, experiment_prefix="obr")`. Returns `{"status": "run"}` or error.

4. **Compare runs:** `from obligation_runtime_telemetry.langsmith import compare_runs` then `compare_runs([run_id_1, run_id_2, ...])`. Requires at least two run IDs; returns `{"status": "compare", "runs": [...], "summary": ...}` or error.

5. **Promote traces to dataset:** `from obligation_runtime_telemetry.langsmith import trace_to_dataset` then `trace_to_dataset(trace_ids, dataset_name)`. Returns `{"status": "promoted", "promoted_count": ...}` or error.

CI: The langsmith job (when configured) runs with LangSmith env; otherwise helpers return `status: "error"` with a clear message.

## Regression corpus

- **Location:** Fixtures under `tests/regressions/fixtures/` and `packages/evals/obligation_runtime_evals/fixtures.py` (patch and multi-agent families). Golden cases in `packages/evals/obligation_runtime_evals/golden.py` and loaders in `golden_cases.py`.

- **Run regressions:** Use the CLI or test suite. Example: `obr regressions` (if wired) or `pytest tests/regressions/ -v`. Golden-case tests load fixtures, run policy/protocol (and optionally the full graph), and assert against canonical reason codes and decisions. See [demos/README.md](../demos/README.md) for regression scenarios and [workflow.md](../workflow.md) for the evaluation flow.

- **Adding cases:** Add JSON fixtures under `tests/regressions/fixtures/` (e.g. `multi_agent_*.json`, `patch_*.json`) with `obligation_input`, `expected_decision`, and optional `expected_trust_level`. Reason codes are canonical in `packages/policy/obligation_runtime_policy/constants.py`.

**See also:** [workflow.md](../workflow.md), [demos/README.md](../demos/README.md), [architecture/telemetry-and-evals.md](../architecture/telemetry-and-evals.md), [running.md](../running.md), [deployment.md](../deployment.md).
