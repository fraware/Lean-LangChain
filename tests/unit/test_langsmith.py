"""Unit tests for LangSmith helpers: create_dataset, run_experiment, compare_runs, trace_to_dataset.

Covers dataset creation (with optional examples), running experiments over a dataset
via run_on_dataset, comparing two or more runs (A/B or evaluator comparison), and
promoting traces to a dataset (trace_to_dataset). When the LangSmith SDK is missing
or auth fails, helpers return status "error" so callers can handle explicitly. These tests
use mocks where needed so CI does not require LANGCHAIN_API_KEY. See
docs/workflow.md (LangSmith integration and tests mapping).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def test_create_dataset_no_exception() -> None:
    """create_dataset with minimal args returns a dict and does not raise. Error when SDK not installed."""
    from obligation_runtime_telemetry.langsmith import create_dataset

    result = create_dataset("test-dataset", description="test")
    assert isinstance(result, dict)
    assert "dataset_name" in result or "status" in result
    assert result.get("dataset_name") == "test-dataset" or result.get("status") in ("error", "created")


def test_run_experiment_no_exception() -> None:
    """run_experiment with minimal args returns a dict and does not raise. Error when SDK not installed."""
    from obligation_runtime_telemetry.langsmith import run_experiment

    def dummy_runnable():
        return lambda x: x

    result = run_experiment("test-dataset", dummy_runnable, experiment_prefix="obr-test")
    assert isinstance(result, dict)
    assert "dataset_name" in result or "status" in result
    assert result.get("status") in ("error", "run")


def test_run_experiment_on_fixed_corpus_returns_expected_status() -> None:
    """Build minimal dataset from fixed corpus (one example), run_experiment with identity runnable; assert status."""
    from obligation_runtime_telemetry.langsmith import create_dataset, run_experiment

    # One example in the format expected by patch-admissibility (input) and output (decision).
    examples = [
        {
            "inputs": {"obligation_input": {"target_files": ["Main.lean"], "current_patch": {}}},
            "outputs": {"expected_decision": "accepted"},
        },
    ]
    ds_result = create_dataset(
        "obr-regression-corpus-test",
        description="Fixed corpus for experiment run test",
        examples=examples,
    )
    assert isinstance(ds_result, dict)
    assert "status" in ds_result

    def identity_runnable():
        return lambda x: x

    exp_result = run_experiment(
        "obr-regression-corpus-test",
        identity_runnable,
        experiment_prefix="obr",
    )
    assert isinstance(exp_result, dict)
    assert "status" in exp_result
    assert exp_result.get("status") in ("run", "error")
    if exp_result.get("status") == "run":
        assert "experiment_prefix" in exp_result
        assert exp_result.get("experiment_prefix") == "obr"


def test_compare_runs_with_mock_client_returns_expected_structure() -> None:
    """With mocked LangSmith client, compare_runs returns runs, summary, status compare."""
    from obligation_runtime_telemetry.langsmith import compare_runs

    mock_run = MagicMock()
    mock_run.inputs = {"x": 1}
    mock_run.outputs = {"y": 2}
    mock_run.error = None
    mock_run.latency_ms = 100

    mock_client = MagicMock()
    mock_client.read_run.return_value = mock_run

    with patch("obligation_runtime_telemetry.langsmith.LangSmithClient", return_value=mock_client):
        result = compare_runs(["run-1", "run-2"])

    assert result.get("status") == "compare"
    assert "runs" in result
    assert len(result["runs"]) == 2
    assert result["runs"][0]["run_id"] == "run-1"
    assert result["runs"][0]["inputs"] == {"x": 1}
    assert result["runs"][0]["outputs"] == {"y": 2}
    assert result["runs"][0]["latency_ms"] == 100
    assert "summary" in result
    assert "2 runs" in result["summary"]
    mock_client.read_run.assert_called()


def test_compare_runs_fewer_than_two_returns_error() -> None:
    """compare_runs with fewer than two run_ids returns error."""
    from obligation_runtime_telemetry.langsmith import compare_runs

    result = compare_runs(["only-one"])
    assert result.get("status") == "error"
    assert result.get("run_ids") == ["only-one"]
    assert "message" in result


def test_trace_to_dataset_with_mock_calls_create_example_from_run() -> None:
    """With mocked client, trace_to_dataset calls create_example_from_run per trace_id."""
    from obligation_runtime_telemetry.langsmith import trace_to_dataset

    mock_run = MagicMock()
    mock_dataset = MagicMock()
    mock_dataset.id = "ds-123"

    mock_client = MagicMock()
    mock_client.list_datasets.return_value = []
    mock_client.create_dataset.return_value = mock_dataset
    mock_client.read_run.return_value = mock_run

    with patch("obligation_runtime_telemetry.langsmith.LangSmithClient", return_value=mock_client):
        result = trace_to_dataset(["trace-a", "trace-b"], "my-dataset")

    assert result.get("status") == "promoted"
    assert result.get("dataset_id") == "ds-123"
    assert result.get("promoted_count") == 2
    assert result.get("run_ids") == ["trace-a", "trace-b"]
    assert mock_client.create_example_from_run.call_count == 2
    mock_client.create_example_from_run.assert_any_call(mock_run, dataset_id="ds-123")
