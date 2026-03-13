"""Integration tests: LangSmith hooks (create_dataset with mock)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def test_langsmith_hooks_create_dataset_with_mock_returns_created() -> None:
    """With mocked LangSmith client, create_dataset returns status created and dataset_id."""
    from obligation_runtime_telemetry.langsmith import create_dataset

    mock_ds = MagicMock()
    mock_ds.id = "ds-123"
    mock_client = MagicMock()
    mock_client.create_dataset.return_value = mock_ds

    with patch("obligation_runtime_telemetry.langsmith.LangSmithClient", return_value=mock_client):
        result = create_dataset("test-ds", description="test")

    assert result.get("status") == "created"
    assert result.get("dataset_id") == "ds-123"
    assert result.get("dataset_name") == "test-ds"
