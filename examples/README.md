# Examples: optional patch producers and minimal SDK usage

**Purpose:** Optional patch producers (fixture, OpenAI, Anthropic) and minimal SDK usage; core runtime does not depend on these. **Audience:** integrators and contributors.

## Minimal: call the Gateway from the SDK

**hello_sdk_gateway.py** – Minimal script for Tier 2 reusers. Run a Gateway, then:

```bash
python examples/hello_sdk_gateway.py
python examples/hello_sdk_gateway.py --repo-path /path/to/lean-repo
```

It opens an environment, creates a session, and runs batch-verify. Use it as a copy-paste starting point when you only need the API client.

## Producer-based demos

- **Producer implementations** – Adapters that implement `CandidateProducer` (e.g. OpenAI, Anthropic, or a fixture that returns a fixed patch). They take context (target files, diagnostics, goals) and return a patch `dict[str, str]` (path to content).
- **run_demo_with_producer.py** – Demo entry point: resolves a producer by name, calls `propose_patch`, sets `current_patch` in state, then invokes the existing graph. The core verification path is unchanged.

## How to run

1. Install the monorepo (orchestrator and dependencies) so that `obligation_runtime_orchestrator` and the SDK are available.
2. For LLM-backed producers, install the provider SDK in your environment (the main project does not depend on them):
   - OpenAI: `pip install openai`
   - Anthropic: `pip install anthropic`
   Or use `examples/requirements.txt`: `pip install -r examples/requirements.txt`
3. Set the required env vars (e.g. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) if using those producers.
4. Start the Gateway if you want to run against it: `uvicorn obligation_runtime_lean_gateway.api.app:app` from the repo root.
5. Run the demo, e.g.:
   ```bash
   python examples/run_demo_with_producer.py --producer fixture --repo-path tests/integration/fixtures/lean-mini --repo-id lean-mini
   ```
   Or with an LLM producer (after installing the SDK and setting the API key):
   ```bash
   python examples/run_demo_with_producer.py --producer openai --repo-path ... --repo-id lean-mini
   ```

## Design rule

The repo may verify LLM-generated Lean, but it does not need to generate Lean itself. All generation is behind the optional producer interface and lives here (or in a separate companion repo), not in the core runtime.

**See also:** [docs/integrate.md](../docs/integrate.md), [docs/demos/README.md](../docs/demos/README.md), [docs/workflow.md](../docs/workflow.md).
