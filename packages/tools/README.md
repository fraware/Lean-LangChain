# Tools

**Purpose:** LangChain tool bindings that expose Gateway operations (open environment, create session, apply patch, batch verify, review). **Audience:** integrators.

This package provides `build_toolset()` and tools for agents to drive the same workflow as the CLI/SDK. Tool callables return the same **Pydantic types** as `ObligationRuntimeClient` (e.g. `OpenEnvironmentResponse`, `BatchVerifyResult`). Serialize with `.model_dump(mode="json")` when feeding results into JSON-only agent pipelines.

See [docs/integrate.md](../../docs/integrate.md) (Tier 3) and [docs/workflow.md](../../docs/workflow.md).

**See also:** [docs/integrate.md](../../docs/integrate.md), [docs/architecture/gateway-api.md](../../docs/architecture/gateway-api.md).
