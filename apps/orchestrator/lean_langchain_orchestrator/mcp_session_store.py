"""MCP session store: persist session context across process restarts.

Backends: memory (default), redis, postgres.
Set OBR_MCP_SESSION_STORE=redis|postgres; Redis: OBR_REDIS_URL;
Postgres: DATABASE_URL or REVIEW_STORE_POSTGRES_URI.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any


class MCPSessionStore(ABC):
    """Backend for persisting MCP session context (session_id, thread_id, etc.)."""

    @abstractmethod
    def get(self, key: str) -> dict[str, Any] | None:
        """Load context by session_id or thread_id. Returns dict or None."""

    @abstractmethod
    def set(
        self,
        session_id: str,
        thread_id: str | None,
        fingerprint_id: str,
        workspace_path: str,
    ) -> None:
        """Persist context. Keyed by session_id and optionally thread_id."""

    @abstractmethod
    def delete(self, session_id: str) -> None:
        """Remove context for session_id."""


class InMemoryMCPSessionStore(MCPSessionStore):
    """In-memory store; context is lost on process restart."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        return self._data.get(key)

    def set(
        self,
        session_id: str,
        thread_id: str | None,
        fingerprint_id: str,
        workspace_path: str,
    ) -> None:
        rec = {
            "session_id": session_id,
            "thread_id": thread_id,
            "fingerprint_id": fingerprint_id,
            "workspace_path": workspace_path,
        }
        self._data[session_id] = rec
        if thread_id:
            self._data[thread_id] = rec

    def delete(self, session_id: str) -> None:
        rec = self._data.pop(session_id, None)
        if rec and rec.get("thread_id"):
            self._data.pop(rec["thread_id"], None)


class RedisMCPSessionStore(MCPSessionStore):
    """Redis-backed store; optional, requires redis package and OBR_REDIS_URL."""

    def __init__(self, url: str | None = None, ttl_seconds: int = 86400) -> None:
        self._url = url or os.environ.get("OBR_REDIS_URL", "")
        self._ttl = ttl_seconds
        self._client: Any = None
        if self._url:
            try:
                import redis

                self._client = redis.from_url(self._url, decode_responses=True)
            except ImportError:
                self._client = None

    def get(self, key: str) -> dict[str, Any] | None:
        if not self._client:
            return None
        try:
            import json

            raw = self._client.get(f"obr:mcp:{key}")
            if raw is None:
                return None
            return json.loads(raw)
        except Exception:
            return None

    def set(
        self,
        session_id: str,
        thread_id: str | None,
        fingerprint_id: str,
        workspace_path: str,
    ) -> None:
        if not self._client:
            return
        import json

        rec = {
            "session_id": session_id,
            "thread_id": thread_id,
            "fingerprint_id": fingerprint_id,
            "workspace_path": workspace_path,
        }
        val = json.dumps(rec)
        try:
            self._client.setex(f"obr:mcp:{session_id}", self._ttl, val)
            if thread_id:
                self._client.setex(f"obr:mcp:{thread_id}", self._ttl, val)
        except Exception:
            pass

    def delete(self, session_id: str) -> None:
        if not self._client:
            return
        try:
            rec = self.get(session_id)
            self._client.delete(f"obr:mcp:{session_id}")
            if rec and rec.get("thread_id"):
                self._client.delete(f"obr:mcp:{rec['thread_id']}")
        except Exception:
            pass


class PostgresMCPSessionStore(MCPSessionStore):
    """Postgres-backed store; uses DATABASE_URL or REVIEW_STORE_POSTGRES_URI."""

    def __init__(self, url: str | None = None) -> None:
        self._url = (
            url or os.environ.get("DATABASE_URL") or os.environ.get("REVIEW_STORE_POSTGRES_URI", "")
        )
        self._table = "obr_mcp_session"

    def _conn(self) -> Any:
        if not self._url:
            return None
        try:
            import psycopg

            return psycopg.connect(self._url)
        except ImportError:
            return None

    def get(self, key: str) -> dict[str, Any] | None:
        conn = self._conn()
        if not conn:
            return None
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT session_id, thread_id, fingerprint_id, workspace_path "
                    f"FROM {self._table} WHERE session_id = %s OR thread_id = %s "
                    "LIMIT 1",
                    (key, key),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    "session_id": row[0],
                    "thread_id": row[1],
                    "fingerprint_id": row[2],
                    "workspace_path": row[3] or "",
                }
        except Exception:
            return None
        finally:
            conn.close()

    def set(
        self,
        session_id: str,
        thread_id: str | None,
        fingerprint_id: str,
        workspace_path: str,
    ) -> None:
        conn = self._conn()
        if not conn:
            return
        try:
            with conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self._table}
                    (session_id TEXT PRIMARY KEY, thread_id TEXT, fingerprint_id TEXT, workspace_path TEXT, updated_at TIMESTAMPTZ DEFAULT NOW())
                    """)
                cur.execute(
                    f"""
                    INSERT INTO {self._table} (session_id, thread_id, fingerprint_id, workspace_path)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (session_id) DO UPDATE SET thread_id = EXCLUDED.thread_id, fingerprint_id = EXCLUDED.fingerprint_id, workspace_path = EXCLUDED.workspace_path, updated_at = NOW()
                    """,
                    (session_id, thread_id or "", fingerprint_id, workspace_path),
                )
            conn.commit()
        except Exception:
            conn.rollback()
        finally:
            conn.close()

    def delete(self, session_id: str) -> None:
        conn = self._conn()
        if not conn:
            return
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"DELETE FROM {self._table} WHERE session_id = %s",
                    (session_id,),
                )
            conn.commit()
        except Exception:
            conn.rollback()
        finally:
            conn.close()


def get_mcp_session_store() -> MCPSessionStore:
    """Return store from OBR_MCP_SESSION_STORE (memory|redis|postgres)."""
    backend = os.environ.get("OBR_MCP_SESSION_STORE", "memory").lower()
    if backend == "redis":
        return RedisMCPSessionStore()
    if backend == "postgres":
        return PostgresMCPSessionStore()
    return InMemoryMCPSessionStore()
