"""Postgres-backed review store. Optional: requires psycopg; enable with REVIEW_STORE=postgres."""

from __future__ import annotations

import json
from typing import Literal

try:
    import psycopg
except ImportError:
    psycopg = None

_TABLE = "obr_reviews"


def _get_conn(uri: str):
    if psycopg is None:
        raise RuntimeError("Postgres review store requires psycopg; pip install psycopg[binary]")
    return psycopg.connect(uri)


def check_connection(uri: str) -> bool:
    """Return True if the database is reachable (for readiness probes)."""
    try:
        with _get_conn(uri) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return True
    except Exception:
        return False


class PostgresReviewStore:
    """Postgres-backed review store. Table: obr_reviews (thread_id, payload JSONB, decision, updated_at)."""

    def __init__(self, connection_uri: str) -> None:
        self._uri = connection_uri
        self._ensure_table()

    def _ensure_table(self) -> None:
        with _get_conn(self._uri) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS obr_reviews (
                        thread_id TEXT PRIMARY KEY,
                        payload JSONB NOT NULL DEFAULT '{}',
                        decision TEXT,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
            conn.commit()

    def put(self, thread_id: str, payload: dict) -> None:
        with _get_conn(self._uri) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO obr_reviews (thread_id, payload, decision, updated_at)
                    VALUES (%s, %s, NULL, NOW())
                    ON CONFLICT (thread_id) DO UPDATE SET
                        payload = EXCLUDED.payload,
                        decision = NULL,
                        updated_at = NOW()
                    """,
                    (thread_id, json.dumps(payload)),
                )
            conn.commit()

    def get(self, thread_id: str) -> dict | None:
        with _get_conn(self._uri) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT payload, decision FROM obr_reviews WHERE thread_id = %s",
                    (thread_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        payload, decision = row
        if isinstance(payload, dict):
            p = payload
        else:
            p = json.loads(payload or "{}")
        return {"payload": p, "decision": decision}

    def get_payload(self, thread_id: str) -> dict | None:
        rec = self.get(thread_id)
        if rec is None:
            return None
        out = dict(rec["payload"])
        if rec.get("decision") is not None:
            out["status"] = rec["decision"]
        return out

    def set_decision(
        self,
        thread_id: str,
        decision: Literal["approved", "rejected"],
    ) -> bool:
        with _get_conn(self._uri) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE obr_reviews SET decision = %s, updated_at = NOW() WHERE thread_id = %s",
                    (decision, thread_id),
                )
                n = cur.rowcount
            conn.commit()
        return n > 0

    def delete(self, thread_id: str) -> bool:
        with _get_conn(self._uri) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM obr_reviews WHERE thread_id = %s", (thread_id,))
                n = cur.rowcount
            conn.commit()
        return n > 0
