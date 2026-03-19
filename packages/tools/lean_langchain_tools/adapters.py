from __future__ import annotations

from typing import Any

from lean_langchain_sdk.client import ObligationRuntimeClient


def make_client(base_url: str, request_adapter: Any = None) -> ObligationRuntimeClient:
    return ObligationRuntimeClient(base_url=base_url, request_adapter=request_adapter)
