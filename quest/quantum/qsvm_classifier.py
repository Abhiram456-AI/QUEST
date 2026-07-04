

"""
QUEST: Quantum Evaluation of Software Trust

Phase 3:
Quantum Trust Intelligence Engine

Module:
Quantum Support Vector Machine Classifier

Purpose:
Performs quantum kernel based trust classification using QUEST
Trust Vectors generated from Phase 2.

Input:
X = [C, D, S, R]
y = Trust reliability classes

Pipeline:
Trust Vector -> Quantum Feature Map -> Quantum Kernel -> QSVC
"""


import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List

import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

from qiskit.circuit.library import ZZFeatureMap
from qiskit_machine_learning.kernels import FidelityQuantumKernel
from qiskit_machine_learning.algorithms import QSVC


@dataclass
class QSVMResult:
    accuracy: float
    feature_dimension: int
    predictions: List[dict]
    classification_metrics: dict


class QUESTQSVMClassifier:
    """
    Quantum Support Vector Machine model for
    reliability-aware trust classification.
    """

    def __init__(self):
        self.model = None
        self.kernel = None


    def build_quantum_kernel(
        self,
        feature_dimension: int
    ):
        """
        Constructs quantum feature encoding.
        """

        feature_map = ZZFeatureMap(
            feature_dimension=feature_dimension,
            reps=2,
            entanglement="linear"
        )

        self.kernel = FidelityQuantumKernel(
            feature_map=feature_map
        )

        self.model = QSVC(
            quantum_kernel=self.kernel
        )


    def train_and_evaluate(
        self,
        X_path: str,
        y_path: str
    ) -> QSVMResult:

        X = np.load(
            X_path
        )

        y = np.load(
            y_path
        )


        if len(X) < 2:
            raise ValueError(
                "QSVM requires multiple training samples"
            )


        self.build_quantum_kernel(
            X.shape[1]
        )


        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.3,
            random_state=42
        )


        self.model.fit(
            X_train,
            y_train
        )


        predictions = self.model.predict(
            X_test
        )


        accuracy = accuracy_score(
            y_test,
            predictions
        )


        prediction_output = []

        for index, prediction in enumerate(predictions):
            prediction_output.append(
                {
                    "sample": index,
                    "actual": int(y_test[index]),
                    "predicted": int(prediction)
                }
            )


        report = classification_report(
            y_test,
            predictions,
            output_dict=True,
            zero_division=0
        )


        return QSVMResult(
            accuracy=float(accuracy),
            feature_dimension=X.shape[1],
            predictions=prediction_output,
            classification_metrics=report
        )


    def save_results(
        self,
        result: QSVMResult,
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
                asdict(result),
                file,
                indent=4
            )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="QUEST Quantum SVM Classifier"
    )

    parser.add_argument(
        "--X",
        default="datasets/X.npy"
    )

    parser.add_argument(
        "--y",
        default="datasets/y.npy"
    )

    parser.add_argument(
        "--output",
        default="outputs/quantum_results/qsvm_results.json"
    )


    args = parser.parse_args()


    qsvm = QUESTQSVMClassifier()

    results = qsvm.train_and_evaluate(
        args.X,
        args.y
    )

    qsvm.save_results(
        results,
        args.output
    )


    print(
        f"QSVM Accuracy: {results.accuracy}"
    )

    print(
        "Quantum Trust Classification Completed"
    )