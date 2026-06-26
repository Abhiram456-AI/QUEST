from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import numpy as np


@dataclass
class QuantumNodeContext:
    """Quantum intelligence attached to a single repository entity."""

    node: str

    # QAOA / Hamiltonian
    risk_energy: float = 0.0
    qaoa_priority: float = 0.0

    # QSVM
    qsvm_classification: str = "UNKNOWN"
    qsvm_confidence: float = 0.0

    # Quantum Walk
    propagation_score: float = 0.0
    stationary_probability: float = 0.0

    # Repository-level influence / uncertainty
    repo_influence: float = 0.0
    uncertainty_score: float = 0.0

    # VQNN
    reliability_score: float = 0.0
    embedding: np.ndarray = field(
        default_factory=lambda: np.array([], dtype=float)
    )

    # Optional metadata for explainability
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node": self.node,
            "risk_energy": round(float(self.risk_energy), 6),
            "qaoa_priority": round(float(self.qaoa_priority), 6),
            "qsvm_classification": self.qsvm_classification,
            "qsvm_confidence": round(float(self.qsvm_confidence), 6),
            "propagation_score": round(float(self.propagation_score), 6),
            "stationary_probability": round(
                float(self.stationary_probability),
                6,
            ),
            "repo_influence": round(
                float(self.repo_influence),
                6,
            ),
            "uncertainty_score": round(
                float(self.uncertainty_score),
                6,
            ),
            "reliability_score": round(
                float(self.reliability_score),
                6,
            ),
            "embedding_dimension": int(len(self.embedding)),
            "metadata": self.metadata,
        }


@dataclass
class QuantumContext:
    """Repository-wide quantum state consumed by MAS agents."""

    nodes: Dict[str, QuantumNodeContext] = field(
        default_factory=dict
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_node(self, context: QuantumNodeContext):
        self.nodes[context.node] = context

    def get_node(
        self,
        node: str,
    ) -> Optional[QuantumNodeContext]:
        return self.nodes.get(node)

    def has_node(self, node: str) -> bool:
        return node in self.nodes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_count": len(self.nodes),
            "nodes": {
                name: node.to_dict()
                for name, node in self.nodes.items()
            },
            "metadata": self.metadata,
        }

    def summary(self) -> Dict[str, Any]:
        if not self.nodes:
            return {
                "node_count": 0,
                "average_reliability": 0.0,
                "average_propagation": 0.0,
                "high_risk_nodes": [],
            }

        reliability = np.array(
            [n.reliability_score for n in self.nodes.values()],
            dtype=float,
        )

        propagation = np.array(
            [n.propagation_score for n in self.nodes.values()],
            dtype=float,
        )

        high_risk_nodes = sorted(
            self.nodes.values(),
            key=lambda n: (
                n.risk_energy,
                n.propagation_score,
            ),
            reverse=True,
        )[:10]

        return {
            "node_count": len(self.nodes),
            "average_reliability": round(
                float(reliability.mean()),
                6,
            ),
            "average_propagation": round(
                float(propagation.mean()),
                6,
            ),
            "high_risk_nodes": [
                {
                    "node": n.node,
                    "risk_energy": round(
                        float(n.risk_energy),
                        6,
                    ),
                    "reliability_score": round(
                        float(n.reliability_score),
                        6,
                    ),
                    "propagation_score": round(
                        float(n.propagation_score),
                        6,
                    ),
                }
                for n in high_risk_nodes
            ],
        }