# Environment model

The environment is the unit of reuse: an immutable base snapshot plus a session-specific writable overlay. See [runtime-graph.md](runtime-graph.md) and [gateway-api.md](gateway-api.md) for context.

For a given repo/commit/toolchain/package state, the system creates:
- an immutable base snapshot
- a session-specific writable overlay

Many sessions may share one base snapshot.
Overlays must never mutate the base snapshot.

**See also:** [runtime-graph.md](runtime-graph.md), [gateway-api.md](gateway-api.md), [worker-isolation.md](worker-isolation.md).
