

"""
QUEST: Quantum Evaluation of Software Trust

Phase 3:
Quantum Trust Intelligence Engine

Module:
QAOA Reliability Optimizer

Purpose:
Uses quantum optimization principles to prioritize software components
for reliability improvement.

Input:
- QUEST Trust Vectors
- Quantum Walk propagation influence

Objective:
Maximize reliability improvement while prioritizing high-impact risks.
"""


import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List

import numpy as np


@dataclass
class QAOAOptimizationResult:
    component: str
    priority_score: float
    trust_score: float
    quantum_priority_rank: int


class QUESTQAOAOptimizer:
    """
    Reliability-aware optimization engine.

    Builds a QAOA-compatible cost objective from:
    - trust risk
    - dependency influence
    - propagation impact
    """


    def calculate_objective(
        self,
        trust_vector: dict,
        propagation_score: float
    ) -> float:

        vector = trust_vector.get(
            "vector",
            [0, 0, 0, 0]
        )

        complexity = vector[0]
        dependency = vector[1]
        security = vector[2]
        reliability = vector[3]

        risk_weight = (
            complexity * 0.3
            + dependency * 0.25
            + security * 0.3
            + propagation_score * 0.15
        )

        improvement_gain = (
            risk_weight
            * (1 - reliability)
        )

        return round(
            improvement_gain,
            5
        )


    def optimize(
        self,
        trust_vector_path: str,
        quantum_walk_path: str
    ) -> List[QAOAOptimizationResult]:

        with open(
            trust_vector_path,
            "r",
            encoding="utf-8"
        ) as file:
            trust_vectors = json.load(file)

        with open(
            quantum_walk_path,
            "r",
            encoding="utf-8"
        ) as file:
            walk_results = json.load(file)


        propagation_lookup = {}

        for result in walk_results:
            scores = result.get(
                "propagation_scores",
                {}
            )

            if scores:
                propagation_lookup.update(scores)


        optimization_results = []

        for component in trust_vectors:

            file_path = component.get(
                "file_path"
            )

            propagation = propagation_lookup.get(
                f"file:{file_path}",
                0
            )

            priority = self.calculate_objective(
                component,
                propagation
            )

            optimization_results.append(
                QAOAOptimizationResult(
                    component=file_path,
                    priority_score=priority,
                    trust_score=component.get(
                        "trust_score"
                    ),
                    quantum_priority_rank=0
                )
            )


        optimization_results.sort(
            key=lambda item: item.priority_score,
            reverse=True
        )

        for index, item in enumerate(
            optimization_results
        ):
            item.quantum_priority_rank = index + 1

        return optimization_results


    def save_results(
        self,
        results: List[QAOAOptimizationResult],
        output_path: str
    ):

        output = Path(output_path)

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
                [asdict(result) for result in results],
                file,
                indent=4
            )


if __name__ == "__main__":

    optimizer = QUESTQAOAOptimizer()

    results = optimizer.optimize(
        "outputs/trust_vectors.json",
        "outputs/quantum_results/quantum_walk_results.json"
    )

    optimizer.save_results(
        results,
        "outputs/quantum_results/qaoa_results.json"
    )

    print(
        "QAOA Reliability Optimization Completed"
    )