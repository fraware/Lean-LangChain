"""Unit tests for PostgresReviewStore. Skip when DATABASE_URL / REVIEW_STORE_POSTGRES_URI not set."""

from __future__ import annotations

import os

import pytest

from lean_langchain_gateway.api.review_store_postgres import PostgresReviewStore


def _get_postgres_uri() -> str | None:
    uri = os.environ.get("REVIEW_STORE_POSTGRES_URI") or os.environ.get("DATABASE_URL")
    return uri if uri else None


@pytest.mark.skipif(
    _get_postgres_uri() is None,
    reason="Postgres not configured: set DATABASE_URL or REVIEW_STORE_POSTGRES_URI",
)
def test_postgres_review_store_put_get_set_decision_delete() -> None:
    """PostgresReviewStore: put, get, set_decision, delete roundtrip when DB available."""
    uri = _get_postgres_uri()
    assert uri is not None
    store = PostgresReviewStore(connection_uri=uri)
    thread_id = "test-thread-postgres-unit-1"
    payload = {"obligation_id": "o1", "summary": "test"}
    store.put(thread_id, payload)
    rec = store.get(thread_id)
    assert rec is not None
    assert rec["payload"].get("obligation_id") == "o1"
    assert rec["decision"] is None

    out = store.get_payload(thread_id)
    assert out is not None
    assert out.get("obligation_id") == "o1"

    ok = store.set_decision(thread_id, "approved")
    assert ok is True
    rec2 = store.get(thread_id)
    assert rec2 is not None
    assert rec2["decision"] == "approved"

    deleted = store.delete(thread_id)
    assert deleted is True
    assert store.get(thread_id) is None
