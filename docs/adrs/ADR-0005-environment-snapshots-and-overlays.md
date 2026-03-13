# ADR-0005 — Environment snapshots and overlays

## Context

Sessions need isolated workspaces for patches and builds without corrupting a shared state. Reuse should happen at the environment (repo + toolchain + deps) level so that many sessions can share one base and only overlay their changes.

## Decision

Immutable base snapshots are keyed by environment fingerprint. Writable overlays are per-session. Reuse occurs at the environment layer, not at the proof-text layer.

## Consequences

- Base is read-only; overlay is per-session writable.
- Many sessions may share one base snapshot; see [environment-model.md](../architecture/environment-model.md) and [worker-isolation.md](../architecture/worker-isolation.md).

**See also:** [environment-model.md](../architecture/environment-model.md), [worker-isolation.md](../architecture/worker-isolation.md), [ADR-0003](ADR-0003-obligation-environment-witness-policy.md).
