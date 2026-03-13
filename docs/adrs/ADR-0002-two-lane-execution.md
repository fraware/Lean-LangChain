# ADR-0002 — Two-lane execution

## Context

We need both fast feedback during development (diagnostics, goals) and a single, authoritative gate for acceptance. Combining them into one path would either sacrifice latency or blur the line between "informational" and "deciding."

## Decision

The runtime uses two lanes:
- **Interactive lane** for low-latency search and repair (diagnostics, goals, hover).
- **Acceptance lane** for authoritative verification (batch build, axiom audit, fresh check).

## Consequences

- Interactive success is necessary but not sufficient for acceptance.
- Acceptance requires batch checks; interactive is never the final gate.

**See also:** [ADR-0001](ADR-0001-lean-is-the-semantic-authority.md), [acceptance-lane.md](../architecture/acceptance-lane.md), [interactive-lane.md](../architecture/interactive-lane.md).
