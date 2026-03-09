from __future__ import annotations

from obligation_runtime_sdk.client import ObligationRuntimeClient


def make_client(base_url: str) -> ObligationRuntimeClient:
    return ObligationRuntimeClient(base_url=base_url)
