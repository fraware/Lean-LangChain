"""Re-export the candidate producer protocol from the orchestrator for convenience."""

from obligation_runtime_orchestrator.producer import (
    CandidateProducer,
    ProducerContext,
    context_from_state,
)

__all__ = ["CandidateProducer", "ProducerContext", "context_from_state"]
