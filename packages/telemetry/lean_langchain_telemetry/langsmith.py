"""LangSmith integration: dataset creation, experiment execution, evaluator comparison, trace promotion."""

from __future__ import annotations

from typing import Any

try:
    from langsmith import Client as LangSmithClient
except ImportError:
    LangSmithClient = None


def patch_admissibility_runnable_factory() -> Any:
    """Return a runnable: inputs (obligation_input, etc.) -> decision/status.
    Compatible with run_on_dataset. Uses policy + protocol path only (no gateway).
    """

    def runnable(inputs: dict[str, Any]) -> dict[str, Any]:
        obligation_input = inputs.get("obligation_input") or inputs
        events = obligation_input.get("protocol_events") or obligation_input.get("events") or []
        obligation_class = obligation_input.get("obligation_class") or "handoff_legality"
        try:
            from lean_langchain_policy.pack_loader import load_pack
            from lean_langchain_policy.protocol_evaluator import (
                evaluate_protocol_obligation,
            )

            pack = load_pack(obligation_input.get("pack_name") or "single_owner_handoff_v1")
        except Exception:
            return {
                "decision": "failed",
                "status": "error",
                "error": "import or load failed",
            }
        if events and obligation_class:
            result = evaluate_protocol_obligation(obligation_class, events, pack)
            return {
                "decision": result.decision,
                "trust_level": result.trust_level,
                "reasons": result.reasons,
            }
        return {"decision": "accepted", "status": "no_events"}

    return runnable


def create_dataset(
    name: str, description: str = "", examples: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Create a dataset; optionally add examples. Returns dataset info or error if SDK unavailable or auth fails."""
    if LangSmithClient is None:
        return {"dataset_name": name, "status": "error", "message": "langsmith not installed"}
    try:
        client = LangSmithClient()
        dataset = client.create_dataset(dataset_name=name, description=description or None)
        if examples:
            client.create_examples(dataset_id=dataset.id, examples=examples)
        return {"dataset_id": str(dataset.id), "dataset_name": name, "status": "created"}
    except Exception as e:
        err = str(e).lower()
        if "401" in err or "unauthorized" in err or "auth" in err or "invalid token" in err:
            return {
                "dataset_name": name,
                "status": "error",
                "message": "auth not configured or invalid",
            }
        return {"dataset_name": name, "status": "error", "error": str(e)}


def run_experiment(
    dataset_name: str,
    runnable: Any,
    experiment_prefix: str = "obr",
) -> dict[str, Any]:
    """Run a runnable over a dataset and record as an experiment. Returns run info or error."""
    if LangSmithClient is None:
        return {
            "dataset_name": dataset_name,
            "status": "error",
            "message": "langsmith not installed",
        }
    try:
        from langsmith import run_on_dataset

        run_on_dataset(
            dataset_name=dataset_name,
            llm_or_chain_factory=runnable,
            experiment_prefix=experiment_prefix,
        )
        return {
            "dataset_name": dataset_name,
            "experiment_prefix": experiment_prefix,
            "status": "run",
        }
    except Exception as e:
        err = str(e).lower()
        if "401" in err or "unauthorized" in err or "auth" in err or "invalid token" in err:
            return {
                "dataset_name": dataset_name,
                "status": "error",
                "message": "auth not configured or invalid",
            }
        return {"dataset_name": dataset_name, "status": "error", "error": str(e)}


def compare_runs(run_ids: list[str]) -> dict[str, Any]:
    """Compare two or more runs (e.g. evaluator comparison). Returns structured comparison or error."""
    if LangSmithClient is None:
        return {"run_ids": run_ids, "status": "error", "message": "langsmith not installed"}
    if len(run_ids) < 2:
        return {"run_ids": run_ids, "status": "error", "message": "at least two run_ids required"}
    try:
        client = LangSmithClient()
        runs: list[dict[str, Any]] = []
        for rid in run_ids:
            try:
                run = client.read_run(rid)
                runs.append(
                    {
                        "run_id": rid,
                        "inputs": getattr(run, "inputs", None) or {},
                        "outputs": getattr(run, "outputs", None) or {},
                        "error": getattr(run, "error", None),
                        "latency_ms": (
                            (getattr(run, "latency_ms", None) or 0)
                            if hasattr(run, "latency_ms")
                            else None
                        ),
                    }
                )
            except Exception as e:
                runs.append({"run_id": rid, "error": str(e)})
        ok = sum(1 for r in runs if not r.get("error"))
        summary = f"{len(runs)} runs; {ok} succeeded, {len(runs) - ok} failed"
        return {
            "run_ids": run_ids,
            "runs": runs,
            "summary": summary,
            "status": "compare",
        }
    except Exception as e:
        err = str(e).lower()
        if "401" in err or "unauthorized" in err or "auth" in err:
            return {"run_ids": run_ids, "status": "error", "message": "auth not configured"}
        return {"run_ids": run_ids, "status": "error", "error": str(e)}


def trace_to_dataset(trace_ids: list[str], dataset_name: str) -> dict[str, Any]:
    """Promote selected traces (run IDs) to a dataset. Creates dataset if needed. Returns dataset info or error."""
    if LangSmithClient is None:
        return {
            "trace_ids": trace_ids,
            "dataset_name": dataset_name,
            "status": "error",
            "message": "langsmith not installed",
        }
    try:
        client = LangSmithClient()
        datasets = list(client.list_datasets(dataset_name=dataset_name))
        if datasets:
            dataset_id = str(datasets[0].id)
        else:
            ds = client.create_dataset(dataset_name=dataset_name)
            dataset_id = str(ds.id)
        promoted = 0
        for tid in trace_ids:
            try:
                run = client.read_run(tid)
                client.create_example_from_run(run, dataset_id=dataset_id)
                promoted += 1
            except Exception:
                pass
        return {
            "dataset_id": dataset_id,
            "dataset_name": dataset_name,
            "promoted_count": promoted,
            "run_ids": trace_ids,
            "status": "promoted",
        }
    except Exception as e:
        err = str(e).lower()
        if "401" in err or "unauthorized" in err or "auth" in err:
            return {
                "trace_ids": trace_ids,
                "dataset_name": dataset_name,
                "status": "error",
                "message": "auth not configured",
            }
        return {
            "trace_ids": trace_ids,
            "dataset_name": dataset_name,
            "status": "error",
            "error": str(e),
        }
