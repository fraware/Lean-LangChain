# LangGraph workflow embedding

Run the patch-admissibility graph from your own Python process. The graph calls the Gateway (open environment, create session, apply patch, interactive check, batch verify, policy review, interrupt for approval, finalize). You can stream events or invoke to completion.

**Prerequisites:** Gateway running. Set `OBR_GATEWAY_URL` (default `http://localhost:8000`). Optional: `CHECKPOINTER=postgres` and `DATABASE_URL` for persistent state and cross-process resume.

**Run:** From repo root with full env (`make install-dev-full`):

```bash
export OBR_GATEWAY_URL=http://localhost:8000
python examples/integrations/langgraph_embed/run_graph.py
```

To embed in your app: use `build_patch_admissibility_graph(gateway_base_url=...)` and `make_initial_state(...)` from `obligation_runtime_orchestrator.runtime`; invoke or stream with your thread_id and config.
