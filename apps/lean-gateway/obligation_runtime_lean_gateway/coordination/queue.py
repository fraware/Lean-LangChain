"""Distributed queue/coordination: Redis when OBR_REDIS_URL set, else in-memory."""

from __future__ import annotations

import json
import os
from collections import deque
from typing import Any, Protocol


def get_redis_url() -> str | None:
    """Return OBR_REDIS_URL or REDIS_URL if set, else None."""
    return (
        os.environ.get("OBR_REDIS_URL") or os.environ.get("REDIS_URL") or None
    )


class CoordinationBackend(Protocol):
    """Minimal coordination: enqueue/dequeue for task distribution."""

    def enqueue(self, queue_name: str, value: str | dict[str, Any]) -> None:
        """Append an item to the queue. If value is dict, JSON-serialize."""
        ...

    def dequeue(self, queue_name: str) -> str | None:
        """Remove and return one item from the queue, or None if empty."""
        ...

    def length(self, queue_name: str) -> int:
        """Return current queue length."""
        ...

    def ping(self) -> bool:
        """Return True if backend is reachable."""
        ...


class InMemoryCoordinationBackend:
    """In-process queues. Not shared across Gateway instances."""

    def __init__(self) -> None:
        self._queues: dict[str, deque[str]] = {}

    def _queue(self, name: str) -> deque[str]:
        if name not in self._queues:
            self._queues[name] = deque()
        return self._queues[name]

    def enqueue(self, queue_name: str, value: str | dict[str, Any]) -> None:
        s = json.dumps(value) if isinstance(value, dict) else value
        self._queue(queue_name).append(s)

    def dequeue(self, queue_name: str) -> str | None:
        q = self._queue(queue_name)
        try:
            return q.popleft()
        except IndexError:
            return None

    def length(self, queue_name: str) -> int:
        return len(self._queue(queue_name))

    def ping(self) -> bool:
        return True


class RedisCoordinationBackend:
    """Redis-backed queues for multi-instance. Requires redis package and OBR_REDIS_URL."""

    def __init__(self, url: str) -> None:
        import redis
        self._client = redis.from_url(url, decode_responses=True)

    def _key(self, queue_name: str) -> str:
        return f"obr:queue:{queue_name}"

    def enqueue(self, queue_name: str, value: str | dict[str, Any]) -> None:
        s = json.dumps(value) if isinstance(value, dict) else value
        self._client.rpush(self._key(queue_name), s)

    def dequeue(self, queue_name: str) -> str | None:
        out = self._client.lpop(self._key(queue_name))
        return out

    def length(self, queue_name: str) -> int:
        return self._client.llen(self._key(queue_name))

    def ping(self) -> bool:
        try:
            return self._client.ping()
        except Exception:
            return False


def get_coordination_backend() -> CoordinationBackend:
    """Return Redis when OBR_REDIS_URL or REDIS_URL set, else in-memory."""
    url = get_redis_url()
    if url:
        try:
            return RedisCoordinationBackend(url)
        except ImportError:
            pass
    return InMemoryCoordinationBackend()
