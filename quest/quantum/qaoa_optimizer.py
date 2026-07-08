"""
QUEST: Quantum Evaluation of Software Trust

Phase 3:
Quantum Trust Intelligence Engine

Module:
QAOA Reliability Optimizer

Purpose:
Uses a simulated Quantum Approximate Optimization Algorithm (QAOA) to solve
a Quadratic Unconstrained Binary Optimization (QUBO) model prioritizing
software components for verification.

Objective:
Maximize reliability improvement under verification resource constraints.
"""

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict

import numpy as np
from scipy.optimize import minimize
from qiskit.circuit import QuantumCircuit
from qiskit.quantum_info import Statevector


@dataclass
class QAOAOptimizationResult:
    component: str
    priority_score: float
    trust_score: float
    quantum_priority_rank: int


class QUESTQAOAOptimizer:
    """
    Reliability-aware quantum optimization engine.
    Solves a resource-constrained QUBO selection problem using QAOA.
    """

    def calculate_objective(
        self,
        trust_vector: dict,
        propagation_score: float
    ) -> float:
        """
        Computes the classical risk improvement objective.
        """
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

    def build_qaoa_circuit(
        self,
        Q: np.ndarray,
        L: np.ndarray,
        gamma: float,
        beta: float
    ) -> QuantumCircuit:
        """
        Compiles the parameterized QAOA ansatz circuit.
        """
        num_qubits = len(L)
        circuit = QuantumCircuit(num_qubits)

        # 1. Initialize uniform superposition state
        for i in range(num_qubits):
            circuit.h(i)

        # 2. Cost Hamiltonian layer: U(H_C, gamma) = exp(-i * H_C * gamma)
        # Linear terms: single-qubit Z-rotations
        for i in range(num_qubits):
            circuit.rz(2 * L[i] * gamma, i)

        # Quadratic terms: ZZ interactions represented by CNOT-Rz-CNOT
        for i in range(num_qubits):
            for j in range(i + 1, num_qubits):
                if abs(Q[i, j]) > 1e-5:
                    circuit.cx(i, j)
                    circuit.rz(2 * Q[i, j] * gamma, j)
                    circuit.cx(i, j)

        # 3. Mixer Hamiltonian layer: U(H_M, beta) = exp(-i * H_M * beta)
        # Single-qubit X-rotations
        for i in range(num_qubits):
            circuit.rx(2 * beta, i)

        return circuit

    def optimize(
        self,
        trust_vector_path: str,
        quantum_walk_path: str
    ) -> List[QAOAOptimizationResult]:
        """
        Runs the hybrid classical-quantum QAOA loop to rank components.
        """
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

        # Map quantum walk risk propagation scores
        propagation_lookup = {}
        for result in walk_results:
            scores = result.get(
                "propagation_scores",
                {}
            )
            if scores:
                propagation_lookup.update(scores)

        # Compute risk objectives for all components
        all_components = []
        for component in trust_vectors:
            file_path = component.get("file_path")
            propagation = propagation_lookup.get(
                f"file:{file_path}",
                0
            )
            obj_score = self.calculate_objective(
                component,
                propagation
            )
            all_components.append({
                "file_path": file_path,
                "trust_score": component.get("trust_score", 0.5),
                "obj_score": obj_score
            })

        # Sort by objective score to identify top candidates
        all_components.sort(
            key=lambda x: x["obj_score"],
            reverse=True
        )

        # Select top components to optimize via QAOA
        # Limit N to 6 to ensure simulation completes in milliseconds
        num_qaoa = min(len(all_components), 6)
        
        if num_qaoa > 0:
            qaoa_candidates = all_components[:num_qaoa]
            
            # Formulate the QUBO problem:
            # Maximize sum(obj_i * x_i) under budget constraint sum(x_i) = k
            # QUBO cost = - sum(obj_i * x_i) + lambda * (sum(x_i) - k)^2
            k = max(1, num_qaoa // 2)
            penalty = 0.5
            
            L = np.zeros(num_qaoa)
            Q = np.zeros((num_qaoa, num_qaoa))
            
            for i in range(num_qaoa):
                # Maximize obj_i -> Minimize -obj_i
                L[i] = -qaoa_candidates[i]["obj_score"]
                # Penalty linear contributions: x_i^2 = x_i -> (1 - 2*k) * penalty
                L[i] += (1 - 2 * k) * penalty
                
            for i in range(num_qaoa):
                for j in range(i + 1, num_qaoa):
                    # Penalty quadratic contributions: 2 * penalty * x_i * x_j
                    Q[i, j] = 2 * penalty
                    Q[j, i] = 2 * penalty

            # Hybrid classical-quantum optimization loop using SciPy COBYLA
            def objective_func(params):
                gamma, beta = params
                qc = self.build_qaoa_circuit(Q, L, gamma, beta)
                sv = Statevector.from_instruction(qc)
                probs = sv.probabilities()
                cost = 0.0
                for state_idx, prob in enumerate(probs):
                    x = np.array([
                        (state_idx >> idx) & 1
                        for idx in range(num_qaoa)
                    ])
                    state_cost = x @ Q @ x + np.dot(L, x)
                    cost += prob * state_cost
                return cost

            # Minimize expectation value classically
            res = minimize(
                objective_func,
                x0=[0.5, 0.5],
                method="COBYLA",
                options={"maxiter": 15}
            )
            
            opt_gamma, opt_beta = res.x
            
            # Evolve final circuit under optimized parameters
            opt_qc = self.build_qaoa_circuit(
                Q, L, opt_gamma, opt_beta
            )
            opt_sv = Statevector.from_instruction(opt_qc)
            final_probs = opt_sv.probabilities()
            
            # Map state probabilities to marginal qubit select probabilities
            # (which represents the quantum-informed priority score)
            for idx in range(num_qaoa):
                marginal_prob = 0.0
                for state_idx, prob in enumerate(final_probs):
                    if (state_idx >> idx) & 1:
                        marginal_prob += prob
                
                # Update priority score with quantum decision probability
                qaoa_candidates[idx]["priority_score"] = round(
                    float(marginal_prob),
                    5
                )
        
        # Compile all results (optimized top N and classical remainder)
        optimization_results = []
        
        for idx, comp in enumerate(all_components):
            if idx < num_qaoa:
                priority = comp.get("priority_score", comp["obj_score"])
            else:
                priority = comp["obj_score"]
                
            optimization_results.append(
                QAOAOptimizationResult(
                    component=comp["file_path"],
                    priority_score=priority,
                    trust_score=comp["trust_score"],
                    quantum_priority_rank=0
                )
            )

        # Sort final results and assign quantum priority rank
        optimization_results.sort(
            key=lambda item: item.priority_score,
            reverse=True
        )

        for index, item in enumerate(optimization_results):
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
    print("QAOA Reliability Optimization Completed")