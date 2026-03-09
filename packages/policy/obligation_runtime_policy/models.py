from __future__ import annotations

from pydantic import Field

from obligation_runtime_schemas.common import StrictModel


class PolicyPack(StrictModel):
    version: str
    name: str
    description: str
    allow_trust_compiler: bool = False
    block_sorry_ax: bool = True
    block_unexpected_custom_axioms: bool = True
    require_human_if_imports_change: bool = True
    protected_paths: list[str] = Field(default_factory=list)
    require_human_on_trust_delta: bool = True
    allow_interactive_warnings: bool = True
