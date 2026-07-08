"""
QUEST: Quantum Evaluation of Software Trust

Phase 3:
Quantum Trust Intelligence Engine

Module:
Quantum Walk Risk Propagation Engine

Purpose:
Uses software graph structures generated in Phase 1 to model
how reliability risk propagates through connected software components.
"""

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
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
        Evolves a true Continuous-Time Quantum Walk (CTQW) across the
        software graph using unitary Schrödinger dynamics.

        H = gamma * L (Graph Laplacian)
        U(t) = exp(-i * H * t)
        |psi(t)> = U(t) |psi(0)>
        P(j, t) = |<j|psi(t)>|^2
        """
        from scipy.linalg import expm
        
        size = adjacency_matrix.shape[0]
        if size == 0:
            return np.array([])
            
        # Symmetrize the adjacency matrix to ensure the Hamiltonian is Hermitian
        # (directed graphs are treated as undirected to preserve unitary evolution)
        A_sym = np.maximum(adjacency_matrix, adjacency_matrix.T)
        
        # Calculate degree matrix diagonal
        degree = A_sym.sum(axis=1)
        D = np.diag(degree)
        
        # Graph Laplacian L = D - A_sym
        L = D - A_sym
        
        # Hamiltonian H = gamma * L, with transmission rate gamma = 0.5
        gamma = 0.5
        H = gamma * L
        
        # Time duration t mapped from step count (e.g. 0.1 per step)
        t = steps * 0.1
        
        # Time-evolution operator U = exp(-i * H * t)
        U = expm(-1j * H * t)
        
        # Initial state |psi(0)>
        psi_0 = np.zeros(size, dtype=complex)
        psi_0[start_index] = 1.0
        
        # Evolved state |psi(t)> = U |psi(0)>
        psi_t = U @ psi_0
        
        # Probability distribution P(j, t) = |psi_j(t)|^2
        probabilities = np.abs(psi_t) ** 2
        
        # Normalize to ensure perfect precision compliance
        total_prob = np.sum(probabilities)
        if total_prob > 0:
            probabilities = probabilities / total_prob
            
        return probabilities

    def analyze(
        self,
        graph_data: Dict
    ) -> QuantumWalkResult:
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        if not nodes:
            raise ValueError("Empty software graph supplied")

        matrix, index_map = self.build_adjacency_matrix(nodes, edges)
        source = nodes[0]
        probabilities = self.quantum_walk(matrix, index_map[source])

        scores = {
            node: round(float(probabilities[index]), 5)
            for node, index in index_map.items()
        }

        ranked = sorted(scores, key=scores.get, reverse=True)

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

        files_data = report.get("files", [])
        all_components = [item.get("file", "") for item in files_data if item.get("file")]
        
        # Build global import graph
        global_nodes = all_components[:]
        global_edges = []
        
        for item in files_data:
            comp = item.get("file", "")
            if not comp:
                continue
            imports_list = item.get("dependencies", {}).get("imports", [])
            for imp in imports_list:
                imp_clean = imp.replace(".", "/")
                for target in all_components:
                    t_no_ext = str(Path(target).with_suffix(""))
                    if t_no_ext.endswith(imp_clean) or imp_clean.endswith(t_no_ext) or imp_clean in t_no_ext:
                        if target != comp:
                            global_edges.append([comp, target])

        results = []
        
        # Run CTQW on the global graph for each source component
        matrix, index_map = self.build_adjacency_matrix(global_nodes, global_edges)
        
        for comp in global_nodes:
            start_idx = index_map[comp]
            probabilities = self.quantum_walk(matrix, start_idx)
            
            # Map probabilities back to file names
            scores = {}
            for node, idx in index_map.items():
                scores[node] = round(float(probabilities[idx]), 5)
                
            ranked = sorted(scores, key=scores.get, reverse=True)
            
            results.append({
                "source_component": comp,
                "propagation_scores": scores,
                "most_influential_components": ranked[:5]
            })

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as file:
            json.dump(results, file, indent=4)

if __name__ == "__main__":
    engine = QuantumWalkEngine()
    engine.analyze_repository(
        "outputs/repository_intelligence.json",
        "outputs/quantum_results/quantum_walk_results.json"
    )
    print("Quantum Walk Risk Propagation Completed")