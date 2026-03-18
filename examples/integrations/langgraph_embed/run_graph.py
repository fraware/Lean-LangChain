"""Minimal example: build and run the patch-admissibility graph against the Gateway.

Run with Gateway up: OBR_GATEWAY_URL=http://localhost:8000 python run_graph.py
"""
from __future__ import annotations

import os

from obligation_runtime_sdk.client import ObligationRuntimeClient
from obligation_runtime_orchestrator.runtime.graph import build_patch_admissibility_graph
from obligation_runtime_orchestrator.runtime.initial_state import make_initial_state

def main() -> None:
    base_url = os.environ.get("OBR_GATEWAY_URL", "http://localhost:8000")
    client = ObligationRuntimeClient(base_url=base_url)
    graph = build_patch_admissibility_graph(client=client)
    initial = make_initial_state(
        thread_id="embed-1",
        obligation_id="ob-1",
        obligation={"target": {"repo_id": "default"}},
        target_files=["Main.lean"],
    )
    config = {"configurable": {"thread_id": initial["thread_id"]}}
    result = graph.invoke(initial, config=config)
    print("Status:", result.get("status"))
    print("Artifacts:", len(result.get("artifacts") or []))

if __name__ == "__main__":
    main()
