"""Experiment runner: delegates to LangSmith when available; returns error otherwise."""

from __future__ import annotations


def run_experiment(name: str, cases: list[dict]) -> dict:
    """Run an experiment over cases. Uses telemetry LangSmith helpers when available."""
    try:
        from obligation_runtime_telemetry.langsmith import (
            create_dataset,
            run_experiment as _run_experiment,
            patch_admissibility_runnable_factory,
        )
    except ImportError:
        return {
            "experiment": name,
            "case_count": len(cases),
            "status": "error",
            "message": "obligation-runtime-telemetry not installed",
        }
    created = create_dataset(name, description=f"Experiment {name}", examples=cases)
    if created.get("status") == "error":
        return {
            "experiment": name,
            "case_count": len(cases),
            "status": "error",
            "message": created.get("message", created.get("error", "create_dataset failed")),
        }
    run_result = _run_experiment(
        dataset_name=name,
        runnable=patch_admissibility_runnable_factory,
        experiment_prefix=name,
    )
    if run_result.get("status") == "error":
        return {
            "experiment": name,
            "case_count": len(cases),
            "status": "error",
            "message": run_result.get("message", run_result.get("error", "run_experiment failed")),
        }
    return {"experiment": name, "case_count": len(cases), "status": "run", "run_result": run_result}
