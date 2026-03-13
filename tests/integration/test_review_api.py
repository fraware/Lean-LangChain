"""Integration tests for Gateway review API: GET/POST reviews, approve, reject."""

from __future__ import annotations

from obligation_runtime_lean_gateway.api import deps


def test_get_review_404_when_no_pending(gateway_client) -> None:
    client = gateway_client
    r = client.get("/v1/reviews/thread-unknown")
    assert r.status_code == 404
    assert r.json().get("error", {}).get("code") == "review_not_found"


def test_create_pending_review_then_get(gateway_client) -> None:
    client = gateway_client
    thread_id = "thread-create-get"
    payload = {
        "thread_id": thread_id,
        "obligation_id": "ob-1",
        "obligation_summary": {"target_files": ["Main.lean"]},
        "reasons": ["protected_path"],
        "status": "awaiting_review",
    }
    create = client.post("/v1/reviews", json=payload)
    assert create.status_code == 200
    assert create.json() == {"ok": True, "thread_id": thread_id}

    get_r = client.get(f"/v1/reviews/{thread_id}")
    assert get_r.status_code == 200
    data = get_r.json()
    assert data["thread_id"] == thread_id
    assert data["obligation_id"] == "ob-1"
    assert data["status"] == "awaiting_review"
    assert "protected_path" in data["reasons"]


def test_create_review_requires_thread_id(gateway_client) -> None:
    client = gateway_client
    r = client.post("/v1/reviews", json={})
    assert r.status_code == 400


def test_approve_and_reject(gateway_client) -> None:
    client = gateway_client
    thread_id = "thread-approve-reject"
    deps.review_store.put(thread_id, {"thread_id": thread_id, "status": "awaiting_review"})

    approve = client.post(f"/v1/reviews/{thread_id}/approve", json={})
    assert approve.status_code == 200
    assert approve.json()["decision"] == "approved"

    get_r = client.get(f"/v1/reviews/{thread_id}")
    assert get_r.status_code == 200
    assert get_r.json()["status"] == "approved"

    thread2 = "thread-reject"
    deps.review_store.put(thread2, {"thread_id": thread2, "status": "awaiting_review"})
    reject = client.post(f"/v1/reviews/{thread2}/reject", json={})
    assert reject.status_code == 200
    assert reject.json()["decision"] == "rejected"
    assert client.get(f"/v1/reviews/{thread2}").json()["status"] == "rejected"


def test_approve_returns_400_when_no_pending(gateway_client) -> None:
    client = gateway_client
    r = client.post("/v1/reviews/no-such-thread/approve", json={})
    assert r.status_code == 400
