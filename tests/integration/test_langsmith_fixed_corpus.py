"""Integration test: run experiment on fixed regression corpus with patch-admissibility runnable.

Loads regression fixtures (e.g. multi_agent_*.json from tests/regressions/fixtures),
builds LangSmith examples in the obligation_input format, creates a dataset,
and runs run_experiment with patch_admissibility_runnable_factory. Validates the
end-to-end LangSmith experiment-on-corpus path used for protocol/regression evaluation.
Skips when fixtures are missing; returns error when LangSmith SDK or auth missing. See
docs/workflow.md (LangSmith integration and use case 2.6).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lean_langchain_telemetry.langsmith import (
    create_dataset,
    patch_admissibility_runnable_factory,
    run_experiment,
)


def test_run_experiment_on_regression_corpus_no_exception() -> None:
    """Load regression corpus, create dataset, run_experiment with patch-admissibility runnable.
    Asserts no unhandled exception; skip when fixtures missing; status is run or error when SDK/env missing.
    """
    fixtures_dir = Path(__file__).resolve().parent.parent / "regressions" / "fixtures"
    if not fixtures_dir.is_dir():
        pytest.skip("regressions/fixtures not found")
    multi_files = list(fixtures_dir.glob("multi_agent_*.json"))
    if not multi_files:
        pytest.skip("no multi_agent fixture JSON files")
    examples = []
    for path in multi_files[:5]:
        raw = json.loads(path.read_text(encoding="utf-8"))
        inp = raw.get("obligation_input") or {}
        if "obligation_class" in inp and "events" in inp:
            examples.append(
                {
                    "inputs": {"obligation_input": inp},
                    "outputs": {
                        "expected_decision": raw.get("expected_decision"),
                        "expected_trust_level": raw.get("expected_trust_level"),
                    },
                }
            )
    if not examples:
        pytest.skip("no obligation_class+events fixtures in regressions/fixtures")
    ds_result = create_dataset(
        "obr-regression-corpus-integration",
        description="Fixed corpus from regression fixtures",
        examples=examples,
    )
    assert isinstance(ds_result, dict)
    assert "status" in ds_result
    runnable = patch_admissibility_runnable_factory
    exp_result = run_experiment(
        "obr-regression-corpus-integration",
        runnable,
        experiment_prefix="obr",
    )
    assert isinstance(exp_result, dict)
    assert exp_result.get("status") in ("run", "error")
    if exp_result.get("status") == "error":
        assert "error" in exp_result
