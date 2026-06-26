from dataclasses import dataclass
from typing import Optional

from quantum.quantum_context import (
    QuantumContext,
    QuantumNodeContext,
)


@dataclass
class QuantumSignals:
    risk_energy: float = 0.0
    qaoa_priority: float = 0.0

    qsvm_classification: str = "UNKNOWN"
    qsvm_confidence: float = 0.0

    propagation_score: float = 0.0
    stationary_probability: float = 0.0

    reliability_score: float = 0.0
    uncertainty_score: float = 1.0


class QuantumAdapter:
    """
    Provides quantum intelligence to MAS agents.
    """

    def __init__(
        self,
        quantum_context: Optional[QuantumContext] = None,
    ):
        self.quantum_context = quantum_context

    def get(
        self,
        node: str,
    ) -> QuantumSignals:
        if self.quantum_context is None:
            return QuantumSignals()

        ctx = self.quantum_context.get_node(node)

        if ctx is None:
            return QuantumSignals()

        uncertainty = (
            1.0 - ctx.qsvm_confidence
        )

        return QuantumSignals(
            risk_energy=ctx.risk_energy,
            qaoa_priority=ctx.qaoa_priority,

            qsvm_classification=ctx.qsvm_classification,
            qsvm_confidence=ctx.qsvm_confidence,

            propagation_score=ctx.propagation_score,
            stationary_probability=ctx.stationary_probability,

            reliability_score=ctx.reliability_score,
            uncertainty_score=uncertainty,
        )