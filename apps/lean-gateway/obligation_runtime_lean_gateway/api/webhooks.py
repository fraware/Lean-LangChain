"""Webhook delivery for review and run lifecycle events.

When OBR_WEBHOOK_URL is set, the gateway POSTs a JSON payload to that URL
for review.created, review.decision, and review.resumed events. Delivery uses
retries with backoff; optional signing via OBR_WEBHOOK_SECRET (HMAC-SHA256 in
X-Webhook-Signature). Receivers should treat events as idempotent (dedupe by
event + thread_id + timestamp).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

_WEBHOOK_TIMEOUT = 10.0
_WEBHOOK_RETRIES = 2
_WEBHOOK_BACKOFF = (1.0, 2.0)


def _webhook_url() -> str | None:
    url = (os.environ.get("OBR_WEBHOOK_URL") or "").strip()
    return url or None


def _webhook_secret() -> bytes | None:
    raw = (os.environ.get("OBR_WEBHOOK_SECRET") or "").strip()
    return raw.encode("utf-8") if raw else None


def _sign_payload(secret: bytes, body: bytes) -> str:
    """HMAC-SHA256 of body, hex-encoded (for X-Webhook-Signature)."""
    return hmac.new(secret, body, hashlib.sha256).hexdigest()


def _emit_event(event_type: str, thread_id: str, payload: dict[str, Any]) -> None:
    """POST event to OBR_WEBHOOK_URL if set. Retries with backoff; optional signing. Use from background task."""
    url = _webhook_url()
    if not url:
        return
    body = {
        "event": event_type,
        "thread_id": thread_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    body_bytes = json.dumps(body, separators=(",", ":")).encode("utf-8")
    secret = _webhook_secret()
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if secret:
        headers["X-Webhook-Signature"] = "sha256=" + _sign_payload(secret, body_bytes)

    import httpx
    last_exc: Exception | None = None
    for attempt in range(_WEBHOOK_RETRIES + 1):
        try:
            with httpx.Client(timeout=_WEBHOOK_TIMEOUT) as client:
                resp = client.post(url, content=body_bytes, headers=headers)
                if resp.status_code < 400:
                    return
                last_exc = RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            last_exc = e
        if attempt < _WEBHOOK_RETRIES:
            time.sleep(_WEBHOOK_BACKOFF[attempt])
    logger.warning("Webhook delivery failed after retries: %s", last_exc, exc_info=False)


def notify_review_created(thread_id: str, payload: dict[str, Any]) -> None:
    """Call after creating a pending review (POST /v1/reviews)."""
    _emit_event("review.created", thread_id, {"payload": payload})


def notify_review_decision(thread_id: str, decision: str) -> None:
    """Call after approve or reject (POST approve/reject)."""
    _emit_event("review.decision", thread_id, {"decision": decision})


def notify_review_resumed(thread_id: str, status: str, artifacts_count: int = 0) -> None:
    """Call after resume completes (POST /v1/reviews/{id}/resume)."""
    _emit_event("review.resumed", thread_id, {"status": status, "artifacts_count": artifacts_count})
