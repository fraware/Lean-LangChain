# Environment Model

The environment is the unit of reuse.

For a given repo/commit/toolchain/package state, the system creates:
- an immutable base snapshot
- a session-specific writable overlay

Many sessions may share one base snapshot.
Overlays must never mutate the base snapshot.
