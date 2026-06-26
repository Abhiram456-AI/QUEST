"""
Risk Hamiltonian construction for QTrustCode.

This module converts normalized repository metrics into a weighted
Hamiltonian representation that can later be optimized by quantum
algorithms such as QAOA.
"""

from __future__ import annotations

from typing import Dict, List


class RiskHamiltonian:
    """
    Builds a weighted risk Hamiltonian from encoded repository metrics.

    Feature order:
        [fan_in, fan_out, centrality,
         blast_radius, instability]
    """

    DEFAULT_WEIGHTS = {
        "fan_in": 0.20,
        "fan_out": 0.25,
        "centrality": 0.20,
        "blast_radius": 0.20,
        "instability": 0.15,
    }

    DEFAULT_INTERACTION_STRENGTH = 0.15

    DEFAULT_INTERACTIONS = {
        ("fan_out", "instability"): 1.40,
        ("centrality", "blast_radius"): 1.30,
        ("fan_in", "centrality"): 1.20,
        ("fan_out", "blast_radius"): 1.10,
    }

    FEATURE_ORDER = [
        "fan_in",
        "fan_out",
        "centrality",
        "blast_radius",
        "instability",
    ]

    def __init__(
        self,
        weights: Dict[str, float] | None = None,
        interaction_strength: float = DEFAULT_INTERACTION_STRENGTH,
    ):
        self.weights = dict(self.DEFAULT_WEIGHTS)

        if weights:
            for feature, value in weights.items():
                if feature in self.weights:
                    self.weights[feature] = float(value)

        try:
            self.interaction_strength = max(
                float(interaction_strength),
                0.0,
            )
        except (TypeError, ValueError):
            self.interaction_strength = (
                self.DEFAULT_INTERACTION_STRENGTH
            )

        self.normalize_weights()
        self.interaction_map = dict(self.DEFAULT_INTERACTIONS)

    def normalize_weights(self) -> None:
        """Ensure all feature weights sum to 1."""
        total = sum(max(weight, 0.0) for weight in self.weights.values())

        if total <= 0:
            self.weights = dict(self.DEFAULT_WEIGHTS)
            total = sum(self.weights.values())

        for feature in self.weights:
            self.weights[feature] = round(
                max(self.weights[feature], 0.0) / total,
                6,
            )

    def sanitize_vector(
        self,
        feature_vector: List[float],
    ) -> List[float]:
        """Convert arbitrary vectors into bounded [0,1] values."""
        values = []

        for index in range(len(self.FEATURE_ORDER)):
            try:
                value = (
                    float(feature_vector[index])
                    if index < len(feature_vector)
                    else 0.0
                )
            except (TypeError, ValueError):
                value = 0.0

            values.append(min(max(value, 0.0), 1.0))

        return values

    def interaction_energy(
        self,
        feature_vector: List[float],
    ) -> float:
        """
        Compute pairwise interaction energy.

        Captures metric interactions such as:
        - high fan_out + high instability
        - high centrality + high blast_radius
        - high fan_in + high centrality
        """
        if not isinstance(feature_vector, (list, tuple)):
            return 0.0

        values = self.sanitize_vector(feature_vector)
        feature_index = {
            feature: idx
            for idx, feature in enumerate(self.FEATURE_ORDER)
        }

        interaction = 0.0

        for pair, multiplier in self.interaction_map.items():
            left_feature, right_feature = pair

            left_idx = feature_index[left_feature]
            right_idx = feature_index[right_feature]

            interaction += (
                values[left_idx]
                * values[right_idx]
                * multiplier
            )

        interaction *= self.interaction_strength
        return round(interaction, 6)

    def energy(self, feature_vector: List[float]) -> float:
        """
        Compute Hamiltonian energy for a single node.

        Lower energy => lower risk
        Higher energy => higher risk
        """
        if not isinstance(feature_vector, (list, tuple)):
            return 0.0

        values = self.sanitize_vector(feature_vector)

        linear_energy = 0.0

        for index, feature in enumerate(self.FEATURE_ORDER):
            linear_energy += (
                values[index]
                * self.weights[feature]
            )

        interaction_energy = self.interaction_energy(feature_vector)
        total_energy = linear_energy + interaction_energy

        return round(max(total_energy, 0.0), 6)

    def build_node_hamiltonian(self, encoded_node: Dict) -> Dict:
        """Construct Hamiltonian representation for one repository node."""
        vector = encoded_node.get("quantum_features", [])
        node = encoded_node.get("node")

        values = self.sanitize_vector(vector)

        linear_energy = sum(
            values[index] * self.weights[feature]
            for index, feature in enumerate(
                self.FEATURE_ORDER
            )
        )

        pairwise_energy = self.interaction_energy(vector)

        return {
            "node": node,
            "quantum_features": vector,
            "weights": dict(self.weights),
            "interaction_strength": self.interaction_strength,
            "linear_energy": round(linear_energy, 6),
            "interaction_energy": pairwise_energy,
            "hamiltonian_formula": (
                "H = "
                f"{self.weights['fan_in']:.3f}·fan_in + "
                f"{self.weights['fan_out']:.3f}·fan_out + "
                f"{self.weights['centrality']:.3f}·centrality + "
                f"{self.weights['blast_radius']:.3f}·blast_radius + "
                f"{self.weights['instability']:.3f}·instability + "
                f"{self.interaction_strength:.3f}·Σ(wᵢⱼ xᵢxⱼ)"
            ),
            "evaluated_formula": (
                f"H = {round(linear_energy, 6)} + "
                f"{round(pairwise_energy, 6)} = "
                f"{round(linear_energy + pairwise_energy, 6)}"
            ),
            "risk_density": round(
                linear_energy + pairwise_energy,
                6,
            ),
            "dominant_metric": max(
                self.FEATURE_ORDER,
                key=lambda feature: (
                    values[
                        self.FEATURE_ORDER.index(feature)
                    ]
                    * self.weights[feature]
                ),
            ),
            "energy": self.energy(vector),
        }

    def build_repository_hamiltonian(
        self,
        encoded_repository: Dict[str, Dict],
    ) -> Dict:
        """Build node Hamiltonians and repository-level statistics."""
        nodes = {}
        total_energy = 0.0

        for node, data in encoded_repository.items():
            payload = {
                "node": node,
                "quantum_features": data.get(
                    "quantum_features",
                    [],
                ),
            }

            result = self.build_node_hamiltonian(payload)
            nodes[node] = result
            total_energy += result["energy"]

        node_count = len(nodes)
        average_energy = (
            total_energy / node_count
            if node_count > 0
            else 0.0
        )

        return {
            "nodes": nodes,
            "repository_energy": round(
                total_energy,
                6,
            ),
            "average_node_energy": round(
                average_energy,
                6,
            ),
            "node_count": node_count,
        }


risk_hamiltonian = RiskHamiltonian()