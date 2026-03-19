"""Integration tests: trace_to_dataset promotes runs to a dataset when LangSmith is available."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def test_dataset_promotion_with_mock_returns_promoted() -> None:
    """With mocked LangSmith client, trace_to_dataset returns status promoted and promoted_count."""
    from lean_langchain_telemetry.langsmith import trace_to_dataset

    mock_run = MagicMock()
    mock_ds = MagicMock()
    mock_ds.id = "ds-456"
    mock_client = MagicMock()
    mock_client.list_datasets.return_value = [mock_ds]
    mock_client.read_run.return_value = mock_run

    with patch("lean_langchain_telemetry.langsmith.LangSmithClient", return_value=mock_client):
        result = trace_to_dataset(["run-1", "run-2"], "my-dataset")

    assert result.get("status") == "promoted"
    assert result.get("dataset_name") == "my-dataset"
    assert result.get("promoted_count") == 2
    assert mock_client.create_example_from_run.call_count == 2
