"""Optional distributed coordination (Redis) for multi-instance Gateway deployments.

When OBR_REDIS_URL is set, use Redis for queue and coordination; otherwise in-memory fallback
(process-local, not suitable for multiple Gateway instances).
"""

from __future__ import annotations

from .queue import get_coordination_backend

__all__ = ["get_coordination_backend"]
