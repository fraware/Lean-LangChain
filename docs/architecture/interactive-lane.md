# Interactive lane

The per-file Lean check path: diagnostics, goals, hover, definition. It informs repair and feedback but never decides acceptance; the acceptance lane does. See [acceptance-lane.md](acceptance-lane.md), [runtime-graph.md](runtime-graph.md), [gateway-api.md](gateway-api.md).

The interactive lane exists for:
- diagnostics
- goal inspection
- hover and definition lookup
- local repair loops

It is explicitly **not** the final acceptance gate.

## Transport boundary

All Lean execution is isolated behind a **transport interface** (`LeanTransport`). The gateway never exposes raw LSP or subprocess output. The interactive API calls the transport to get raw diagnostics and goals, then normalizes them via `InteractiveNormalizer` into schema-shaped responses. Production requires `OBR_USE_REAL_LEAN` or `OBR_USE_LEAN_LSP`. Tests inject a test double (`TestDoubleTransport`) via `deps.set_test_transport()` in conftest. See ADR-0006.

**See also:** [acceptance-lane.md](acceptance-lane.md), [gateway-api.md](gateway-api.md), [runtime-graph.md](runtime-graph.md), [adrs/ADR-0006-interactive-transport-boundary.md](../adrs/ADR-0006-interactive-transport-boundary.md).
