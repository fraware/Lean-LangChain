# ADR-0005 — Environment snapshots and overlays

Immutable base snapshots are keyed by environment fingerprint.
Writable overlays are per-session.
Reuse occurs at the environment layer, not at the proof-text layer.
