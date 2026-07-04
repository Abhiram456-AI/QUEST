

"""
QUEST: Quantum Evaluation of Software Trust

Phase 3:
Quantum Trust Intelligence Engine

Module:
Quantum Variational Neural Network Predictor

Purpose:
Uses variational quantum learning to predict software reliability
from QUEST Trust Vectors.

Input:
T = [C, D, S, R]

Output:
Future reliability probability estimation.
"""


import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List

import numpy as np

from qiskit.circuit import QuantumCircuit, ParameterVector
from qiskit.quantum_info import Statevector


@dataclass
class QVNNPrediction:
    sample_id: int
    reliability_probability: float
    predicted_state: str


class QUESTQVNNPredictor:
    """
    Variational quantum reliability predictor.

    Encodes trust vectors into quantum states and applies
    parameterized rotations to estimate reliability behavior.
    """

    def __init__(self):
        self.parameters = None


    def build_variational_circuit(
        self,
        features: List[float]
    ):
        """
        Builds a parameterized quantum neural circuit.
        """

        qubits = len(features)

        circuit = QuantumCircuit(
            qubits
        )

        theta = ParameterVector(
            "theta",
            qubits
        )

        self.parameters = theta


        for index, value in enumerate(features):
            circuit.ry(
                value * np.pi,
                index
            )


        for index in range(qubits - 1):
            circuit.cx(
                index,
                index + 1
            )


        for index in range(qubits):
            circuit.ry(
                theta[index],
                index
            )


        return circuit


    def predict_sample(
        self,
        features: List[float]
    ) -> float:

        circuit = self.build_variational_circuit(
            features
        )


        parameter_values = {
            parameter: np.pi / 4
            for parameter in self.parameters
        }

        circuit = circuit.assign_parameters(
            parameter_values
        )


        state = Statevector.from_instruction(
            circuit
        )


        probabilities = state.probabilities()


        reliability_probability = float(
            np.sum(
                probabilities[len(probabilities)//2:]
            )
        )


        return round(
            reliability_probability,
            5
        )


    def predict(
        self,
        X_path: str
    ) -> List[QVNNPrediction]:

        X = np.load(
            X_path
        )

        predictions = []


        for index, sample in enumerate(X):

            probability = self.predict_sample(
                sample.tolist()
            )


            if probability >= 0.7:
                state = "HIGH_RELIABILITY"

            elif probability >= 0.4:
                state = "MODERATE_RELIABILITY"

            else:
                state = "LOW_RELIABILITY"


            predictions.append(
                QVNNPrediction(
                    sample_id=index,
                    reliability_probability=probability,
                    predicted_state=state
                )
            )


        return predictions


    def save_results(
        self,
        predictions: List[QVNNPrediction],
        output_path: str
    ):

        output = Path(
            output_path
        )

        output.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        with open(
            output,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                [asdict(item) for item in predictions],
                file,
                indent=4
            )


if __name__ == "__main__":

    predictor = QUESTQVNNPredictor()

    predictions = predictor.predict(
        "datasets/X.npy"
    )

    predictor.save_results(
        predictions,
        "outputs/quantum_results/qvnn_results.json"
    )


    print(
        "QVNN Reliability Prediction Completed"
    )