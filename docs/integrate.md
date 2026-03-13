# How to integrate

Integration tiers (data contracts only, API client, LangChain tools, full graph, host the Gateway) and public API reference. **Recommended entry point:** Tier 2 (API client).

Choose a tier based on what you need. All install commands assume you are in the repo root and use the same Python (e.g. an activated venv). When installing from this repo, install in order or use `make install-dev-full` for the full stack. If packages are published, you can depend on them by name (e.g. `obligation-runtime-sdk`).

**Local install order:** schemas, evals, telemetry, protocol, policy, sdk-py, tools, lean-gateway, orchestrator. Running `make install-dev-full` does this in one step. Tier 4 and protocol-related flows require the `protocol` package; `make install-dev-full` includes it.

---

## Tier 1 — Data contracts only

**When to use:** You only need the Python types and schemas (e.g. `WitnessBundle`, `EnvironmentFingerprint`, `BatchVerifyResult`) in your own code or to talk to a Gateway via your own HTTP client.

**Install:**

```bash
python -m pip install -e packages/schemas
```

**Usage:** Import from `obligation_runtime_schemas` (see `packages/schemas/obligation_runtime_schemas/__init__.py` for exports).

---

## Tier 2 — API client (recommended entry point)

**When to use:** You want to call an existing Obligation Runtime Gateway from your Python app. You do not need to host the Gateway or run the full graph; you only need a client that talks to a running Gateway.

**Install:**

```bash
python -m pip install -e packages/schemas -e packages/sdk-py
```

**Usage:** Create a client and point it at the Gateway base URL:

```python
from obligation_runtime_sdk import ObligationRuntimeClient

client = ObligationRuntimeClient(base_url="http://localhost:8000")
# Open environment, create session, apply patch, interactive-check, batch-verify, etc.
resp = client.open_environment(repo_id="my-repo", repo_path="/path/to/repo")
```

This is the **best single entry point** for reusers: one client, one base URL. See `examples/minimal_sdk_gateway.py` for a minimal script. For runnable demos (patch verification, review), see [docs/demos/](demos/README.md) and `make demo-core` / `make demo-full`.

---

## Tier 3 — LangChain tools

**When to use:** You want to expose verification (open environment, create session, apply patch, check, batch-verify, etc.) as LangChain tools so an agent can call the Gateway.

**Install:**

```bash
python -m pip install -e packages/tools
```

This pulls in `obligation-runtime-sdk` and `obligation-runtime-schemas`.

**Usage:** Build a toolset from a client and pass the tools to your agent:

```python
from obligation_runtime_sdk import ObligationRuntimeClient
from obligation_runtime_tools import build_toolset

client = ObligationRuntimeClient(base_url="http://localhost:8000")
tools = build_toolset("http://localhost:8000", client=client)
# Use tools with your LangChain/LangGraph agent
```

---

## Tier 4 — Full graph (orchestrator)

**When to use:** You want to run the full patch-admissibility graph (interactive check, batch verify, policy, review, finalize) via the CLI or programmatically, against a Gateway.

**Install:**

```bash
python -m pip install -e apps/orchestrator
```

This pulls in `obligation-runtime-schemas`, `obligation-runtime-sdk`, and `obligation-runtime-policy`.

**Usage:** Use the CLI (`obr`) or import the graph builder:

```bash
obr open-environment --repo-id lean-mini --repo-path /path/to/repo
obr create-session --fingerprint-id <id>
obr run-patch-obligation ...
```

Or programmatically:

```python
from obligation_runtime_orchestrator import (
    build_patch_admissibility_graph,
    ObligationRuntimeState,
    make_initial_state,
)
# Build graph with client; create initial state with make_initial_state(...); invoke.
```

---

## Public API

Recommended top-level imports per package:

| Package | Import | Purpose |
|---------|--------|---------|
| **obligation_runtime_schemas** | `EnvironmentFingerprint`, `BatchVerifyResult`, `WitnessBundle`, etc. | Data contracts and Pydantic models for Gateway payloads. |
| **obligation_runtime_sdk** | `ObligationRuntimeClient`, `RequestAdapter` | Call the Gateway from Python; optional custom adapter for tests or in-process use. |
| **obligation_runtime_tools** | `build_toolset` | Build LangChain tools that call the Gateway. Fixed order: open_environment, create_session, apply_patch, check_interactive, get_goal, hover, definition, batch_verify, get_review_payload, submit_review_decision. |
| **obligation_runtime_orchestrator** | `build_patch_admissibility_graph`, `ObligationRuntimeState`, `make_initial_state`, `CandidateProducer`, `context_from_state` | Run the patch-admissibility graph; build initial state; implement or use producers. |
| **obligation_runtime_policy** | Policy pack loading and decision types | Policy engine and pack evaluation. |
| **obligation_runtime_protocol** | Protocol event types and evaluation | Protocol compliance and evaluator. |
| **obligation_runtime_telemetry** | Tracer and span types | Observability and LangSmith integration. |
| **obligation_runtime_evals** | Golden cases, loaders | Evaluation corpus and regression harness. |

---

## Tier 5 — Host the Gateway

**When to use:** You want to run the Lean Gateway (FastAPI server) so that others (or your own clients) can call it via the SDK or tools.

**Install:**

```bash
python -m pip install -e packages/schemas -e apps/lean-gateway
```

**Usage:** Start the server:

```bash
uvicorn obligation_runtime_lean_gateway.api.app:app --reload
```

OpenAPI at `/docs` and `/redoc`. See [running.md](running.md) for full setup.

---

## Optional packages

- **evals** — Evaluation corpus, experiments, and regression runners.
- **telemetry** — Tracer and LangSmith integration; optional OTLP and langsmith extras.
- **examples** — Minimal SDK script only. Not required for core verification; see `examples/README.md`. Demos are in scripts/demos and docs/demos.
- **review-ui** — Next.js UI for review/approve/reject and resume. Consumes the Gateway API; run from `apps/review-ui`.

---

## Summary

| Goal | Tier | Install |
|------|------|--------|
| Data contracts only | 1 | `pip install -e packages/schemas` |
| Call a Gateway from Python | 2 (recommended) | `pip install -e packages/schemas -e packages/sdk-py` |
| LangChain tools for agents | 3 | `pip install -e packages/tools` |
| Run full patch-admissibility graph | 4 | `pip install -e apps/orchestrator` |
| Host the Gateway | 5 | `pip install -e packages/schemas -e apps/lean-gateway` |

For local development of the full repo, use `make install-dev-full` as in the main README.

**See also:** [workflow.md](workflow.md), [architecture/gateway-api.md](architecture/gateway-api.md), [running.md](running.md), [README.md](../README.md).
