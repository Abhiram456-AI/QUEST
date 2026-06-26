

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

import numpy as np

try:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    QISKIT_AVAILABLE = True
except Exception:
    QuantumCircuit = None
    Statevector = None
    QISKIT_AVAILABLE = False


@dataclass
class VQNNResult:
    predictions: Dict[str, float]
    embeddings: Dict[str, np.ndarray]
    loss_history: List[float] = field(default_factory=list)
    epochs: int = 0
    backend: str = "classical"


class VariationalQuantumNeuralNetwork:
    """
    Quantum-inspired VQNN for reliability-aware code verification.

    Input features:
    - normalized risk metrics
    - repository influence
    - propagation risk
    - QAOA energies
    - QSVM confidence
    - quantum walk scores

    Output:
    Reliability score in [0, 1].
    """

    def __init__(
        self,
        n_qubits: int = 4,
        n_layers: int = 2,
        learning_rate: float = 0.05,
        seed: Optional[int] = 42,
    ):
        self.n_qubits = max(2, n_qubits)
        self.n_layers = max(1, n_layers)
        self.learning_rate = learning_rate
        self.rng = np.random.default_rng(seed)

        self.weights = self.rng.uniform(
            -np.pi,
            np.pi,
            size=(self.n_layers, self.n_qubits),
        )

    def _coerce_feature_mapping(self, feature_vectors: Any) -> Dict[str, np.ndarray]:
        """Normalize supported feature container formats into a node->feature mapping."""
        if feature_vectors is None:
            return {}

        if not isinstance(feature_vectors, dict):
            raise TypeError("feature_vectors must be a dictionary mapping node names to feature vectors.")

        normalized: Dict[str, np.ndarray] = {}

        for node, value in feature_vectors.items():
            if isinstance(value, dict):
                features = value.get("quantum_features")
                if features is None:
                    features = value.get("features")
                if features is None:
                    continue
                value = features

            array = np.asarray(value, dtype=float)
            array = np.nan_to_num(array, nan=0.0, posinf=0.0, neginf=0.0)
            normalized[node] = array

        return normalized

    def _normalize(self, vector: np.ndarray) -> np.ndarray:
        vector = np.nan_to_num(vector.astype(float))

        if vector.size == 0:
            return np.zeros(self.n_qubits)

        if vector.size < self.n_qubits:
            vector = np.pad(
                vector,
                (0, self.n_qubits - vector.size),
            )
        else:
            vector = vector[: self.n_qubits]

        maximum = np.max(np.abs(vector))
        if maximum > 0:
            vector = vector / maximum

        return vector

    def _classical_forward(self, x: np.ndarray):
        state = x.copy()

        for layer in self.weights:
            state = np.tanh(state + np.sin(layer))

        score = float((np.mean(state) + 1.0) / 2.0)
        score = float(np.clip(score, 0.0, 1.0))

        return score, state

    def _quantum_forward(self, x: np.ndarray):
        if not QISKIT_AVAILABLE:
            return self._classical_forward(x)

        qc = QuantumCircuit(self.n_qubits)

        for i, value in enumerate(x):
            qc.ry(float(value * np.pi), i)

        for layer in self.weights:
            for q in range(self.n_qubits):
                qc.rx(float(layer[q]), q)

            for q in range(self.n_qubits - 1):
                qc.cx(q, q + 1)

        statevector = Statevector.from_instruction(qc)
        probabilities = statevector.probabilities()

        score = float(np.max(probabilities))
        embedding = probabilities[: self.n_qubits]

        return score, embedding

    def predict(
        self,
        feature_vectors: Dict[str, np.ndarray],
    ) -> VQNNResult:
        feature_vectors = self._coerce_feature_mapping(feature_vectors)

        if not feature_vectors:
            return VQNNResult(
                predictions={},
                embeddings={},
                epochs=0,
                backend=("qiskit-statevector" if QISKIT_AVAILABLE else "classical"),
            )

        predictions = {}
        embeddings = {}

        backend = (
            "qiskit-statevector"
            if QISKIT_AVAILABLE
            else "classical"
        )

        for node, vector in feature_vectors.items():
            x = self._normalize(vector)

            if QISKIT_AVAILABLE:
                score, embedding = self._quantum_forward(x)
            else:
                score, embedding = self._classical_forward(x)

            predictions[node] = round(score, 4)
            embeddings[node] = np.nan_to_num(
                np.asarray(embedding, dtype=float),
                nan=0.0,
                posinf=0.0,
                neginf=0.0,
            )

        return VQNNResult(
            predictions=predictions,
            embeddings=embeddings,
            epochs=0,
            backend=backend,
        )