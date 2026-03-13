# ADR-0001 — Lean is the semantic authority

## Context

The system must decide whether a patch or change is acceptable. That decision must rest on a single, unambiguous semantic authority so that evidence is reproducible and auditable. Lean (build, axiom audit, fresh checker) provides that authority for the code under verification.

## Decision

Lean is the only formal semantic authority in the system.

## Consequences

- The model may propose, but may not self-certify.
- Interactive results inform repair loops.
- Acceptance is determined only by Lean + policy.
- Policy decides operational admissibility, not theorem validity.

**See also:** [acceptance-lane.md](../architecture/acceptance-lane.md), [interactive-lane.md](../architecture/interactive-lane.md).
