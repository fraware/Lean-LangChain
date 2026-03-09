# ADR-0002 — Two-lane execution

## Decision
The runtime uses two lanes:
- interactive lane for low-latency search and repair
- acceptance lane for authoritative verification

## Consequences
- Interactive success is necessary but not sufficient.
- Acceptance requires batch checks.
