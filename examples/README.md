# Examples: minimal SDK usage

**Purpose:** A single minimal script showing how to call the Lean-LangChain Gateway from Python. The core runtime does not depend on this. **Audience:** integrators (Tier 2 reusers) who need a copy-paste starting point.

**Demos** (patch verification, review flow, evidence bundle) live in **scripts/demos/** and are documented in **[docs/demos/](../docs/demos/)**. Run `make demo-core` or `make demo-full` for the full flows.

---

## minimal_sdk_gateway.py

Opens an environment, creates a session, and runs batch-verify. No graph, no CLI; just the SDK and the Gateway API. The Python SDK returns **Pydantic models** (e.g. `open_resp.fingerprint_id`, `batch_data.trust_level`), not plain dicts.

**Run:** Start the Gateway (`uvicorn lean_langchain_gateway.api.app:app`), then:

```bash
python examples/minimal_sdk_gateway.py
python examples/minimal_sdk_gateway.py --repo-path /path/to/lean-repo
```

Use it as a starting point when you only need the API client. For the full verification and review demos, see [docs/demos/README.md](../docs/demos/README.md).

**Integration starters** (MCP tool builder, LangGraph embed, policy pack extension): see [examples/integrations/](integrations/README.md).

**See also:** [docs/integrate.md](../docs/integrate.md), [docs/demos/](../docs/demos/).
