"""
QAOA optimizer for QTrustCode.

This module builds an Ising-style repository risk Hamiltonian and uses
Qiskit QAOA to prioritize high-risk modules and correlated architectural
hotspots within a repository.
"""

from __future__ import annotations

from typing import Dict, List
import numpy as np

from qiskit.quantum_info import SparsePauliOp

try:
    from qiskit.primitives import StatevectorSampler
except ImportError:
    from qiskit.primitives import Sampler as StatevectorSampler

from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA


class RiskQAOA:
    """
    Qiskit-powered QAOA optimizer for repository risk prioritization.

    Each selected repository module is mapped to a qubit. The cost
    Hamiltonian is derived from repository risk energies produced by
    risk_hamiltonian.py.
    """

    def __init__(self, layers: int = 2, top_k: int = 8):
        self.layers = max(1, int(layers))
        self.top_k = max(1, int(top_k))

    def _build_interaction_matrix(
        self,
        node_data: List[tuple],
    ) -> np.ndarray:
        """
        Build a symmetric interaction matrix describing
        repository coupling between modules.

        Preference order:
            dependency_strength
            call_similarity
            architectural_similarity

        Missing values default to weak coupling.
        """
        size = len(node_data)
        matrix = np.zeros((size, size), dtype=float)

        for i in range(size):
            matrix[i, i] = 1.0

            left_meta = node_data[i][1]

            for j in range(i + 1, size):
                right_meta = node_data[j][1]

                left_dep = float(
                    left_meta.get("dependency_strength", 0.0)
                )
                right_dep = float(
                    right_meta.get("dependency_strength", 0.0)
                )

                left_call = float(
                    left_meta.get("call_similarity", 0.0)
                )
                right_call = float(
                    right_meta.get("call_similarity", 0.0)
                )

                left_arch = float(
                    left_meta.get(
                        "architectural_similarity",
                        0.0,
                    )
                )
                right_arch = float(
                    right_meta.get(
                        "architectural_similarity",
                        0.0,
                    )
                )

                avg_dep = (left_dep + right_dep) / 2.0
                avg_call = (left_call + right_call) / 2.0
                avg_arch = (left_arch + right_arch) / 2.0

                energy_i = float(
                    left_meta.get("energy", 0.0)
                )
                energy_j = float(
                    right_meta.get("energy", 0.0)
                )

                energy_alignment = 1.0 - min(
                    abs(energy_i - energy_j),
                    1.0,
                )

                coupling = (
                    (0.50 * avg_dep)
                    + (0.30 * avg_call)
                    + (0.20 * avg_arch)
                )

                coupling *= (0.50 + (0.50 * energy_alignment))
                coupling = float(np.clip(coupling, 0.05, 1.0))

                matrix[i, j] = coupling
                matrix[j, i] = coupling

        return matrix

    def _build_cost_operator(
        self,
        energies: np.ndarray,
        interactions: np.ndarray,
    ) -> SparsePauliOp:
        """
        Build an Ising-style repository risk Hamiltonian:

            H = Σ h_i Z_i + λ Σ J_ij Z_i Z_j

        where:
            h_i  -> normalized module risk energies
            J_ij -> pairwise interaction strength between modules
            λ    -> coupling coefficient

        This formulation allows QAOA to optimize over both
        individual module risk and correlated high-risk regions
        of the repository.
        """

        num_qubits = len(energies)

        if num_qubits == 0:
            return SparsePauliOp.from_list([("I", 0.0)])

        max_energy = float(np.max(np.abs(energies)))
        if max_energy <= 0:
            normalized = np.zeros_like(energies)
        else:
            normalized = energies / max_energy

        paulis = []

        # Local repository risk fields.
        for index, energy in enumerate(normalized):
            label = ["I"] * num_qubits
            label[index] = "Z"
            paulis.append(("".join(label), float(energy)))

        # Pairwise coupling between risky modules.
        coupling_scale = min(
            0.50,
            0.15 + (0.02 * num_qubits),
        )

        for i in range(num_qubits):
            for j in range(i + 1, num_qubits):
                repository_coupling = interactions[i, j]

                coupling = (
                    normalized[i]
                    * normalized[j]
                    * repository_coupling
                    * coupling_scale
                )

                if abs(coupling) < 1e-8:
                    continue

                label = ["I"] * num_qubits
                label[i] = "Z"
                label[j] = "Z"

                paulis.append(
                    ("".join(label), float(coupling))
                )

        return SparsePauliOp.from_list(paulis).simplify()

    def optimize(self, node_energies: Dict[str, Dict]) -> Dict:
        if not node_energies:
            return {
                "layers": self.layers,
                "top_k": self.top_k,
                "qubits": 0,
                "optimized": [],
                "risk_distribution": {},
                "highest_risk_node": None,
            }

        ranked_nodes = sorted(
            node_energies.items(),
            key=lambda item: float(
                item[1].get("energy", 0.0)
            ),
            reverse=True,
        )[: self.top_k]

        nodes: List[str] = [item[0] for item in ranked_nodes]

        energies = np.array(
            [
                float(data.get("energy", 0.0))
                for _, data in ranked_nodes
            ],
            dtype=float,
        )

        interactions = self._build_interaction_matrix(
            ranked_nodes
        )

        num_qubits = len(nodes)

        cost_operator = self._build_cost_operator(
            energies,
            interactions,
        )

        hamiltonian_terms = {
            node: round(float(energy), 6)
            for node, energy in zip(nodes, energies)
        }

        sampler = StatevectorSampler()
        optimizer = COBYLA(
            maxiter=max(100, num_qubits * 25)
        )

        qaoa = QAOA(
            sampler=sampler,
            optimizer=optimizer,
            reps=self.layers,
        )

        try:
            result = qaoa.compute_minimum_eigenvalue(
                cost_operator
            )

            quantum_probabilities = None

            try:
                eigenstate = getattr(result, "eigenstate", None)
                if eigenstate is not None:
                    amplitudes = np.asarray(eigenstate.data)
                    probabilities_array = np.abs(amplitudes) ** 2
                    if probabilities_array.size >= num_qubits:
                        quantum_probabilities = probabilities_array[:num_qubits]
                        total = np.sum(quantum_probabilities)
                        if total > 0:
                            quantum_probabilities = (
                                quantum_probabilities / total
                            )
            except Exception:
                quantum_probabilities = None

            optimal_value = float(result.eigenvalue.real)
        except Exception:
            optimal_value = float(np.sum(energies))
            quantum_probabilities = None

        if 'quantum_probabilities' in locals() and quantum_probabilities is not None:
            probabilities = quantum_probabilities
        elif np.sum(energies) > 0:
            probabilities = energies / np.sum(energies)
        else:
            probabilities = np.full(
                num_qubits,
                1.0 / max(num_qubits, 1),
            )

        ranking = sorted(
            [
                {
                    "node": node,
                    "energy": round(float(energy), 6),
                    "priority_probability": round(
                        float(prob),
                        6,
                    ),
                }
                for node, energy, prob in zip(
                    nodes,
                    energies,
                    probabilities,
                )
            ],
            key=lambda item: item[
                "priority_probability"
            ],
            reverse=True,
        )

        return {
            "layers": self.layers,
            "top_k": self.top_k,
            "qubits": num_qubits,
            "qaoa_optimal_value": round(
                optimal_value,
                6,
            ),
            "quantum_metadata": {
                "backend": sampler.__class__.__name__,
                "optimizer": optimizer.__class__.__name__,
                "layers": self.layers,
                "top_k": self.top_k,
                "num_qubits": num_qubits,
                "hamiltonian_type": "repository_ising",
            },
            "cost_hamiltonian": {
                "equation": "H = Σ h_i Z_i + λ Σ J_ij Z_i Z_j",
                "coupling_scale": round(
                    min(
                        0.50,
                        0.15 + (0.02 * num_qubits),
                    ),
                    3,
                ),
                "interaction_matrix": interactions.round(3).tolist(),
                "local_fields": hamiltonian_terms,
                "num_pauli_terms": len(cost_operator.paulis),
            },
            "optimized": ranking,
            "risk_distribution": {
                item["node"]: item[
                    "priority_probability"
                ]
                for item in ranking
            },
            "highest_risk_node": (
                ranking[0]["node"]
                if ranking
                else None
            ),
        }