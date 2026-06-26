from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Union

import numpy as np

from collections import deque


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        v = float(value)
        if np.isnan(v) or np.isinf(v):
            return default
        return v
    except (ValueError, TypeError):
        return default


@dataclass
class QuantumWalkResult:
    transition_matrix: np.ndarray
    amplitudes: np.ndarray
    probabilities: np.ndarray
    stationary_distribution: np.ndarray
    propagation_scores: Dict[str, float]
    high_impact_modules: List[str]
    propagation_paths: List[Dict[str, Any]]
    walk_history: List[np.ndarray]
    steps: int = 0
    convergence_history: List[float] = field(default_factory=list)
    entropy_history: List[float] = field(default_factory=list)
    node_index: Dict[str, int] = field(default_factory=dict)
    final_entropy: float = 0.0
    converged: bool = False


class QuantumWalkEngine:
    """
    Quantum-inspired walk engine for repository dependency propagation.

    Nodes  -> repository modules/files
    Edges  -> dependency relationships
    State  -> risk amplitudes

    Purpose:
        Model how risk originating in one module propagates throughout
        the repository graph.
    """

    def __init__(
        self,
        walk_steps: int = 10,
        damping: float = 0.85,
        convergence_tol: float = 1e-6,
        min_probability: float = 1e-12,
    ):
        # Validate and clamp constructor arguments
        self.walk_steps = walk_steps if walk_steps >= 1 else 1
        self.damping = min(max(damping, 0.0), 1.0)
        self.convergence_tol = convergence_tol if convergence_tol > 0 else 1e-6
        self.min_probability = min_probability if min_probability > 0 else 1e-12

        self.node_index: Dict[str, int] = {}
        self.index_node: Dict[int, str] = {}

        self.transition_matrix: Optional[np.ndarray] = None
        self.last_result: Optional[QuantumWalkResult] = None

    def _normalize_dependencies(self, dependencies: Any) -> Dict[str, List[str]]:
        """Normalize supported dependency graph representations into an adjacency mapping."""
        if dependencies is None:
            return {}

        if isinstance(dependencies, dict):
            return dependencies

        # Support NetworkX-like graphs without importing networkx.
        if hasattr(dependencies, "adj"):
            normalized: Dict[str, List[str]] = {}
            for node, neighbors in dependencies.adj.items():
                normalized[str(node)] = [str(n) for n in neighbors]
            return normalized

        if hasattr(dependencies, "adjacency"):
            normalized: Dict[str, List[str]] = {}
            for node, neighbors in dependencies.adjacency():
                normalized[str(node)] = [str(n) for n in neighbors]
            return normalized

        raise TypeError("Unsupported dependency graph type.")

    def _build_transition_matrix(
        self,
        dependencies: Optional[Dict[Any, Optional[List[Any]]]],
        repository_metrics: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> np.ndarray:
        # Defensive input normalization
        dependencies = self._normalize_dependencies(dependencies)

        # Filter keys to strings only
        filtered_deps = {}
        for source, targets in dependencies.items():
            if not isinstance(source, str):
                continue
            if targets is None:
                targets = []
            filtered_targets = [t for t in targets if isinstance(t, str)]
            filtered_deps[source] = filtered_targets
        dependencies = filtered_deps

        nodes = sorted(
            set(dependencies.keys())
            | {
                dep
                for deps in dependencies.values()
                for dep in deps
            }
        )

        n = len(nodes)

        self.node_index = {}
        self.index_node = {}

        if n == 0:
            return np.zeros((0, 0), dtype=float)

        self.node_index = {
            node: i
            for i, node in enumerate(nodes)
        }
        self.index_node = {
            i: node
            for node, i in self.node_index.items()
        }

        matrix = np.zeros((n, n), dtype=float)

        for source, targets in dependencies.items():
            i = self.node_index.get(source)
            if i is None:
                continue

            if not targets:
                # Uniform fallback if no targets
                matrix[i, :] = 1.0 / n
                continue

            edge_weights: List[Tuple[int, float]] = []

            for target in targets:
                j = self.node_index.get(target)
                if j is None:
                    continue

                metrics = {}
                if repository_metrics:
                    metrics = repository_metrics.get(target, {})

                # Defensive numeric conversions with fallback
                pagerank = safe_float(metrics.get("pagerank", 0.0))
                centrality = safe_float(metrics.get("centrality", 0.0))
                blast_radius = safe_float(metrics.get("blast_radius", 0.0))
                propagation_risk = safe_float(metrics.get("propagation_risk", 0.0))

                weight = (
                    0.30 * pagerank
                    + 0.25 * centrality
                    + 0.25 * blast_radius
                    + 0.20 * propagation_risk
                )

                if weight <= 0:
                    weight = 1.0  # Graceful fallback for non-positive weights

                edge_weights.append((j, weight))

            total_weight = sum(w for _, w in edge_weights)
            if not edge_weights:
                # Uniform fallback if no valid edges
                matrix[i, :] = 1.0 / n
                continue
            if total_weight <= 0:
                total_weight = float(len(edge_weights))  # Uniform fallback

            for j, weight in edge_weights:
                matrix[i, j] = weight / total_weight

        # Teleportation matrix for damping
        teleport = np.ones((n, n), dtype=float) / n
        matrix = (
            self.damping * matrix
            + (1.0 - self.damping) * teleport
        )

        # Normalize rows and sanitize NaNs/Infs
        row_sums = matrix.sum(axis=1, keepdims=True)
        # Replace zero or near-zero rows with uniform distribution
        for idx, s in enumerate(row_sums.flatten()):
            if s <= self.min_probability:
                matrix[idx, :] = 1.0 / n
                row_sums[idx, 0] = 1.0

        matrix = matrix / row_sums
        matrix = np.nan_to_num(
            matrix,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        # Verify rows sum to ~1.0, fix zero rows if any remain
        for idx in range(n):
            row_sum = matrix[idx, :].sum()
            if not np.isfinite(row_sum) or row_sum <= self.min_probability:
                matrix[idx, :] = 1.0 / n

        return matrix

    def propagate_risk(
        self,
        dependencies: Dict[str, List[str]],
        initial_risk: Dict[str, Any],
        repository_metrics: Optional[Dict[str, Dict[str, float]]] = None,
        steps: Optional[int] = None,
    ) -> QuantumWalkResult:
        # Reset transient state at start
        self.node_index.clear()
        self.index_node.clear()
        self.transition_matrix = None
        self.last_result = None

        steps = steps or self.walk_steps
        steps = max(1, int(steps))

        matrix = self._build_transition_matrix(dependencies, repository_metrics)
        self.transition_matrix = matrix

        n = matrix.shape[0]

        if initial_risk is None:
            initial_risk = {}
        elif not isinstance(initial_risk, dict):
            raise TypeError("initial_risk must be a dictionary.")

        if n == 0:
            result = QuantumWalkResult(
                transition_matrix=np.zeros((0, 0)),
                amplitudes=np.array([]),
                probabilities=np.array([]),
                stationary_distribution=np.array([]),
                propagation_scores={},
                high_impact_modules=[],
                propagation_paths=[],
                walk_history=[],
                steps=0,
                convergence_history=[],
                entropy_history=[],
                node_index={},
                final_entropy=0.0,
                converged=True,
            )
            self.last_result = result
            return result

        amplitudes = np.zeros(n, dtype=float)

        # Sanitize initial risk inputs
        for node, score in initial_risk.items():
            if node in self.node_index:
                try:
                    val = float(score)
                    if not np.isfinite(val) or val < 0:
                        val = 0.0
                    amplitudes[self.node_index[node]] = val
                except (ValueError, TypeError):
                    continue

        total = amplitudes.sum()
        if total <= 0:
            amplitudes[:] = 1.0 / n  # Uniform fallback
        else:
            amplitudes /= total

        state = np.sqrt(amplitudes.copy())
        walk_history: List[np.ndarray] = [state.copy()]
        convergence_history: List[float] = []
        entropy_history: List[float] = []

        for _ in range(steps):
            previous_state = state.copy()

            # Sanitize state vector before multiplication
            state = np.nan_to_num(
                state,
                nan=0.0,
                posinf=0.0,
                neginf=0.0,
            )

            state = np.asarray(
                state @ matrix,
                dtype=float,
            ).reshape(-1)

            # Verify dimension consistency
            if state.shape[0] != n:
                raise RuntimeError("Quantum walk state dimension mismatch.")

            # Sanitize state vector after multiplication
            state = np.nan_to_num(
                state,
                nan=0.0,
                posinf=0.0,
                neginf=0.0,
            )

            # Preserve quantum amplitude normalization
            norm = np.linalg.norm(state)
            if norm > self.min_probability:
                state = state / norm

            delta = float(
                np.linalg.norm(state - previous_state)
            )
            convergence_history.append(delta)

            probabilities_snapshot = np.abs(state) ** 2
            prob_sum = probabilities_snapshot.sum()
            if prob_sum > 0:
                probabilities_snapshot /= prob_sum

            entropy = float(
                -np.sum(
                    probabilities_snapshot
                    * np.log2(
                        np.clip(
                            probabilities_snapshot,
                            self.min_probability,
                            None,
                        )
                    )
                )
            )
            entropy_history.append(entropy)

            walk_history.append(state.copy())

            if delta < self.convergence_tol:
                break

        probabilities = np.abs(state) ** 2

        probabilities = np.nan_to_num(
            probabilities,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        prob_total = probabilities.sum()
        if prob_total > 0:
            probabilities /= prob_total

        probabilities = np.nan_to_num(
            probabilities,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        if probabilities.sum() <= 0:
            probabilities = np.full(n, 1.0 / n)  # Uniform fallback
        else:
            probabilities /= probabilities.sum()

        try:
            eigvals, eigvecs = np.linalg.eig(matrix.T)
            idx = int(
                np.argmin(
                    np.abs(eigvals - 1)
                )
            )
            stationary = np.real_if_close(
                eigvecs[:, idx]
            ).astype(float)
        except Exception:
            stationary = probabilities.copy()  # Eigen fallback

        stationary = np.abs(stationary)
        stationary = np.nan_to_num(
            stationary,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        stationary_sum = stationary.sum()
        if stationary_sum > 0:
            stationary /= stationary_sum
        else:
            stationary = np.full(n, 1.0 / n)  # Uniform fallback

        # Defensive array checks for propagation scores
        def sanitize_array(arr: np.ndarray) -> np.ndarray:
            if (
                arr.ndim != 1
                or arr.shape[0] != n
                or not np.all(np.isfinite(arr))
            ):
                return np.full(n, 1.0 / n)
            return arr

        probabilities = sanitize_array(probabilities)
        stationary = sanitize_array(stationary)
        amplitudes = sanitize_array(amplitudes)

        propagation_scores = {
            self.index_node[i]: float(
                round(
                    max(
                        probabilities[i],
                        stationary[i],
                    ),
                    6,
                )
            )
            for i in range(n)
        }
        propagation_scores = {
            str(k): float(v)
            for k, v in propagation_scores.items()
        }

        ranked = sorted(
            propagation_scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        high_impact_modules = [
            module
            for module, _ in ranked[:5]
        ]

        propagation_paths = []

        max_depth = min(3, steps)

        nonzero_mask = np.logical_or(
            probabilities > self.min_probability,
            stationary > self.min_probability,
        )

        for source in self.node_index:
            source_idx = self.node_index[source]

            if (
                source_idx >= len(nonzero_mask)
                or not nonzero_mask[source_idx]
            ):
                continue

            frontier = deque([(source_idx, 1.0, 0)])
            visited = set()

            while frontier:
                current_idx, probability, depth = frontier.popleft()

                if depth >= max_depth:
                    continue

                row = matrix[current_idx]

                for next_idx, edge_prob in enumerate(row):
                    if (
                        edge_prob <= self.min_probability
                        or next_idx >= len(nonzero_mask)
                        or not nonzero_mask[next_idx]
                    ):
                        continue

                    state_key = (
                        source_idx,
                        next_idx,
                        depth + 1,
                    )

                    if state_key in visited:
                        continue

                    visited.add(state_key)

                    cumulative = probability * float(edge_prob)
                    if not np.isfinite(cumulative) or cumulative < 0:
                        continue  # Ignore invalid cumulative probabilities

                    target = self.index_node[next_idx]

                    propagation_paths.append(
                        {
                            "source": source,
                            "target": target,
                            "probability": round(cumulative, 6),
                            "path_length": depth + 1,
                        }
                    )

                    frontier.append(
                        (
                            next_idx,
                            cumulative,
                            depth + 1,
                        )
                    )

        propagation_paths.sort(
            key=lambda x: (
                x["probability"],
                -x["path_length"],
            ),
            reverse=True,
        )

        stationary = np.asarray(
            stationary,
            dtype=float,
        ).reshape(-1)
        probabilities = np.asarray(
            probabilities,
            dtype=float,
        ).reshape(-1)
        amplitudes = np.asarray(
            amplitudes,
            dtype=float,
        ).reshape(-1)

        # Sanitize walk history, convergence, and entropy histories
        def sanitize_list(lst: List[Union[float, np.ndarray]]) -> List:
            sanitized = []
            for item in lst:
                if isinstance(item, np.ndarray):
                    if item.ndim == 1 and np.all(np.isfinite(item)):
                        sanitized.append(item)
                else:
                    try:
                        val = float(item)
                        if np.isfinite(val):
                            sanitized.append(val)
                    except Exception:
                        continue
            return sanitized

        walk_history = sanitize_list(walk_history)
        convergence_history = sanitize_list(convergence_history)
        entropy_history = sanitize_list(entropy_history)

        result = QuantumWalkResult(
            transition_matrix=matrix,
            amplitudes=amplitudes,
            probabilities=probabilities,
            stationary_distribution=stationary,
            propagation_scores=propagation_scores,
            high_impact_modules=high_impact_modules,
            propagation_paths=propagation_paths[:20],
            walk_history=walk_history,
            steps=steps,
            convergence_history=convergence_history,
            entropy_history=entropy_history,
            node_index=dict(self.node_index),
            final_entropy=(
                entropy_history[-1]
                if entropy_history
                else 0.0
            ),
            converged=(
                convergence_history[-1]
                < self.convergence_tol
                if convergence_history
                else True
            ),
        )

        self.last_result = result
        return result

    def get_summary(self) -> Dict[str, Any]:
        if self.last_result is None:
            return {}

        return {
            "nodes": len(self.node_index),
            "steps": self.last_result.steps,
            "top_propagation_modules": (
                self.last_result.high_impact_modules
            ),
            "top_propagation_paths": (
                self.last_result.propagation_paths[:5]
            ),
            "walk_iterations": len(
                self.last_result.walk_history
            ),
            "final_state_norm": (
                float(
                    np.linalg.norm(
                        self.last_result.walk_history[-1]
                    )
                )
                if self.last_result.walk_history
                else 0.0
            ),
            "converged": self.last_result.converged,
            "last_convergence_delta": (
                float(
                    self.last_result.convergence_history[-1]
                )
                if self.last_result.convergence_history
                else 0.0
            ),
            "final_entropy": (
                self.last_result.final_entropy
            ),
            "stationary_entropy": float(
                -np.sum(
                    self.last_result.stationary_distribution
                    * np.log2(
                        np.clip(
                            self.last_result.stationary_distribution,
                            self.min_probability,
                            None,
                        )
                    )
                )
            ) if len(self.last_result.stationary_distribution) else 0.0,
            "max_propagation_score": max(
                self.last_result.propagation_scores.values(),
                default=0.0,
            ),
            "transition_matrix_shape": (
                self.last_result.transition_matrix.shape
                if self.last_result.transition_matrix is not None
                else (0, 0)
            ),
            "stationary_distribution_sum": float(
                np.sum(self.last_result.stationary_distribution)
                if self.last_result.stationary_distribution is not None
                else 0.0
            ),
            "transition_matrix_available": self.last_result.transition_matrix is not None,
            "propagation_node_count": len(self.last_result.propagation_scores),
        }