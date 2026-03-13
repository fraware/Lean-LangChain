# ADR-0003 — Obligation, environment, witness, policy

## Context

To keep the system auditable and composable, all major data crossing service boundaries should be typed and versioned. Ad hoc payloads would make it hard to replay, compare, or reason about runs.

## Decision

The public system revolves around four primitives: **Obligation**, **EnvironmentFingerprint**, **WitnessBundle**, **PolicyDecision**. No service boundary may invent ad hoc payloads when one of these primitives applies.

## Consequences

- Schemas and APIs are defined in terms of these primitives.
- Witness bundles carry full evidence for accepted runs; environment fingerprint pins the Lean/Lake context.

**See also:** [core-primitives.md](../architecture/core-primitives.md), [glossary.md](../glossary.md).
