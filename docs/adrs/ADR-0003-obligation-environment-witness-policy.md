# ADR-0003 — Canonical primitives

The public system revolves around four primitives:
- Obligation
- EnvironmentFingerprint
- WitnessBundle
- PolicyDecision

No service boundary may invent ad hoc payloads when one of these primitives applies.
