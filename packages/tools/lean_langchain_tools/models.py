from __future__ import annotations

from lean_langchain_schemas.common import StrictModel


class GatewayConfig(StrictModel):
    base_url: str = "http://localhost:8000"
