from __future__ import annotations

from obligation_runtime_schemas.witness import WitnessBundle


def build_witness_bundle(*, bundle_id: str, obligation_id: str, environment_fingerprint: dict, interactive: dict, acceptance: dict, policy: dict, approval: dict | None = None, trace: dict | None = None) -> WitnessBundle:
    return WitnessBundle(
        bundle_id=bundle_id,
        obligation_id=obligation_id,
        environment_fingerprint=environment_fingerprint,  # type: ignore[arg-type]
        interactive=interactive,  # type: ignore[arg-type]
        acceptance=acceptance,
        policy=policy,  # type: ignore[arg-type]
        approval=approval or {},
        trace=trace or {},
    )
