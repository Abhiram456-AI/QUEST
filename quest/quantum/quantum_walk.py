

"""
QUEST: Quantum Evaluation of Software Trust

Phase 3:
Quantum Trust Intelligence Engine

Module:
Quantum Walk Risk Propagation Engine

Purpose:
Uses software graph structures generated in Phase 1 to model
how reliability risk propagates through connected software components.

Input:
Software Graph G(V,E)

Output:
Component influence probabilities for reliability-aware verification.
"""


import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict

import numpy as np


@dataclass
class QuantumWalkResult:
    source_component: str
    propagation_scores: Dict[str, float]
    most_influential_components: List[str]


class QuantumWalkEngine:
    """
    Performs quantum-inspired probability evolution over
    QUEST software dependency graphs.
    """

    def build_adjacency_matrix(
        self,
        nodes: List[str],
        edges: List[List[str]]
    ):

        index_map = {
            node: index
            for index, node in enumerate(nodes)
        }

        matrix = np.zeros(
            (len(nodes), len(nodes))
        )

        for source, target in edges:
            if source in index_map and target in index_map:
                matrix[
                    index_map[source]
                ][
                    index_map[target]
                ] = 1

        return matrix, index_map


    def quantum_walk(
        self,
        adjacency_matrix,
        start_index,
        steps=10
    ):
        """
        Evolves probability amplitudes across the
        software graph using a normalized transition operator.

        Ensures valid probability distribution:

            0 <= probability <= 1
            sum(probabilities) = 1
        """

        size = adjacency_matrix.shape[0]

        state = np.zeros(size)
        state[start_index] = 1.0


        degree = adjacency_matrix.sum(axis=1)

        transition = np.zeros_like(
            adjacency_matrix,
            dtype=float
        )


        for index in range(size):

            if degree[index] > 0:
                transition[index] = (
                    adjacency_matrix[index]
                    / degree[index]
                )

            else:
                # Preserve probability mass for isolated nodes
                transition[index][index] = 1.0


        for _ in range(steps):

            state = transition.T @ state

            total_probability = np.sum(
                np.abs(state)
            )

            if total_probability > 0:
                state = state / total_probability


        return np.abs(state)


    def analyze(
        self,
        graph_data: Dict
    ) -> QuantumWalkResult:

        nodes = graph_data.get(
            "nodes",
            []
        )

        edges = graph_data.get(
            "edges",
            []
        )

        if not nodes:
            raise ValueError(
                "Empty software graph supplied"
            )

        matrix, index_map = self.build_adjacency_matrix(
            nodes,
            edges
        )

        source = nodes[0]

        probabilities = self.quantum_walk(
            matrix,
            index_map[source]
        )

        scores = {
            node: round(float(probabilities[index]), 5)
            for node, index in index_map.items()
        }

        ranked = sorted(
            scores,
            key=scores.get,
            reverse=True
        )

        return QuantumWalkResult(
            source_component=source,
            propagation_scores=scores,
            most_influential_components=ranked[:5]
        )


    def analyze_repository(
        self,
        intelligence_path: str,
        output_path: str
    ):

        with open(
            intelligence_path,
            "r",
            encoding="utf-8"
        ) as file:
            report = json.load(file)

        results = []

        for item in report.get("files", []):

            if "graph" not in item:
                continue

            try:
                result = self.analyze(
                    item["graph"]
                )

                results.append(
                    asdict(result)
                )

            except Exception:
                continue


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
                results,
                file,
                indent=4
            )


if __name__ == "__main__":

    engine = QuantumWalkEngine()

    engine.analyze_repository(
        "outputs/repository_intelligence.json",
        "outputs/quantum_results/quantum_walk_results.json"
    )

    print(
        "Quantum Walk Risk Propagation Completed"
    )