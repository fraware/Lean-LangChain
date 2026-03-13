# ADR-0006 — Interactive lane transport boundary

## Context

The interactive lane needs to call Lean (LSP or subprocess) for diagnostics and goals. Exposing raw LSP or subprocess output at the API would couple clients to wire format and make it hard to swap implementations or normalize responses.

## Decision

The interactive lane talks to a **transport interface** (`LeanTransport`), not to raw subprocess or LSP. The gateway normalizes all results before returning them to clients.

## Consequences

- No raw LSP wire format is exposed at the API boundary.
- Production requires a real transport (`OBR_USE_REAL_LEAN` or `OBR_USE_LEAN_LSP`). Tests inject a test double via `deps.set_test_transport(TestDoubleTransport())` in conftest.
- A real Lean/LSP implementation can be plugged in by providing another implementation of `LeanTransport.check(session_id, file_path) -> (raw_diagnostics, raw_goals, ok)`.

**See also:** [interactive-lane.md](../architecture/interactive-lane.md), [gateway-api.md](../architecture/gateway-api.md).
