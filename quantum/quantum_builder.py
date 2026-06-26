from __future__ import annotations

from typing import Any, Dict, Optional, Iterable

import numpy as np

from quantum.quantum_context import (
    QuantumContext,
    QuantumNodeContext,
)


class QuantumContextBuilder:
    """
    Aggregates outputs from all quantum modules and produces a
    repository-wide QuantumContext that can be consumed by MAS agents.
    """

    def __init__(self):
        self.context = QuantumContext()

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, value))

    @staticmethod
    def _normalize_node_key(
        node: Any,
    ) -> str:
        return str(node).strip().replace("\\", "/")

    @staticmethod
    def _lookup_by_node(
        mapping: Any,
        node: str,
        default: Any = None,
    ) -> Any:
        if not isinstance(mapping, dict):
            return default

        normalized = (
            QuantumContextBuilder
            ._normalize_node_key(node)
        )

        if normalized in mapping:
            return mapping[normalized]

        basename = normalized.split("/")[-1]
        for key, value in mapping.items():
            candidate = (
                QuantumContextBuilder
                ._normalize_node_key(key)
            )
            if (
                candidate == normalized
                or candidate.endswith(normalized)
                or normalized.endswith(candidate)
                or candidate.split("/")[-1] == basename
            ):
                return value

        return default

    def build(
        self,
        repository_nodes: Iterable[str],
        qaoa_result: Optional[Any] = None,
        qsvm_result: Optional[Any] = None,
        quantum_walk_result: Optional[Any] = None,
        vqnn_result: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> QuantumContext:
        self.context = QuantumContext(
            metadata=metadata or {}
        )
        repository_nodes = list(
            repository_nodes or []
        )
        repository_metrics = (
            (metadata or {}).get(
                "repository_metrics",
                {},
            )
        )
        if not isinstance(
            repository_metrics,
            dict,
        ):
            repository_metrics = {}
        qaoa_enabled = qaoa_result is not None
        qsvm_enabled = qsvm_result is not None
        quantum_walk_enabled = (
            quantum_walk_result is not None
        )
        vqnn_enabled = vqnn_result is not None

        energies = {}
        priorities = {}
        classifications = {}
        confidences = {}
        propagation_scores = {}
        stationary = np.array([])
        node_index = {}
        predictions = {}
        embeddings = {}

        if qaoa_enabled:
            if isinstance(qaoa_result, dict):
                energies = qaoa_result.get(
                    "energies",
                    {},
                )
                priorities = qaoa_result.get(
                    "priorities",
                    {},
                )
            else:
                energies = getattr(
                    qaoa_result,
                    "energies",
                    {},
                )
                priorities = getattr(
                    qaoa_result,
                    "priorities",
                    {},
                )

        if qsvm_enabled:
            if isinstance(qsvm_result, dict):
                # Backward compatible: if top-level keys exist, use them
                if "classifications" in qsvm_result or "confidences" in qsvm_result:
                    classifications = qsvm_result.get(
                        "classifications",
                        {},
                    )
                    confidences = qsvm_result.get(
                        "confidences",
                        {},
                    )
                else:
                    # New per-node mapping format
                    classifications = {
                        node: info.get("predicted_class", "UNKNOWN")
                        for node, info in qsvm_result.items()
                        if isinstance(info, dict)
                    }
                    confidences = {
                        node: info.get("risk_probability", 0.0)
                        for node, info in qsvm_result.items()
                        if isinstance(info, dict)
                    }
            else:
                classifications = getattr(
                    qsvm_result,
                    "classifications",
                    {},
                )
                confidences = getattr(
                    qsvm_result,
                    "confidences",
                    {},
                )

        # Defensive normalization for QSVM dicts
        if not isinstance(classifications, dict):
            classifications = {}
        if not isinstance(confidences, dict):
            confidences = {}

        if quantum_walk_enabled:
            if isinstance(quantum_walk_result, dict):
                propagation_scores = (
                    quantum_walk_result.get(
                        "propagation_scores",
                        {},
                    )
                )
                stationary = (
                    quantum_walk_result.get(
                        "stationary_distribution",
                        np.array([]),
                    )
                )
                node_index = (
                    quantum_walk_result.get(
                        "node_index",
                        {},
                    )
                )
            else:
                propagation_scores = getattr(
                    quantum_walk_result,
                    "propagation_scores",
                    {},
                )
                stationary = getattr(
                    quantum_walk_result,
                    "stationary_distribution",
                    np.array([]),
                )
                node_index = getattr(
                    quantum_walk_result,
                    "node_index",
                    {},
                )

        if vqnn_enabled:
            if isinstance(vqnn_result, dict):
                predictions = vqnn_result.get(
                    "predictions",
                    {},
                )
                embeddings = vqnn_result.get(
                    "embeddings",
                    {},
                )
            else:
                predictions = getattr(
                    vqnn_result,
                    "predictions",
                    {},
                )
                embeddings = getattr(
                    vqnn_result,
                    "embeddings",
                    {},
                )

        stationary = np.asarray(
            stationary,
            dtype=float,
        ).reshape(-1)
        stationary = np.nan_to_num(
            stationary,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        for node in repository_nodes:
            normalized_node = (
                self._normalize_node_key(node)
            )
            idx = None
            metrics = {}
            node_context = QuantumNodeContext(node=node)

            # ---------- QAOA ----------
            if qaoa_enabled:
                node_context.risk_energy = self._safe_float(
                    self._lookup_by_node(
                        energies,
                        normalized_node,
                        0.0,
                    )
                )
                node_context.qaoa_priority = self._clamp(
                    self._safe_float(
                        self._lookup_by_node(
                            priorities,
                            normalized_node,
                            0.0,
                        )
                    )
                )

            # ---------- QSVM ----------
            if qsvm_enabled:
                node_context.qsvm_classification = (
                    self._lookup_by_node(
                        classifications,
                        normalized_node,
                        "UNKNOWN",
                    )
                )
                node_context.qsvm_confidence = self._clamp(
                    self._safe_float(
                        self._lookup_by_node(
                            confidences,
                            normalized_node,
                            0.0,
                        )
                    )
                )

            # ---------- Quantum Walk ----------
            if quantum_walk_enabled:
                node_context.propagation_score = self._clamp(
                    self._safe_float(
                        self._lookup_by_node(
                            propagation_scores,
                            normalized_node,
                            0.0,
                        )
                    )
                )

                idx = self._lookup_by_node(
                    node_index,
                    normalized_node,
                )
                try:
                    idx = (
                        int(idx)
                        if idx is not None
                        else None
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    idx = None
                if (
                    idx is not None
                    and idx >= 0
                    and stationary.size > idx
                ):
                    node_context.stationary_probability = (
                        self._clamp(
                            self._safe_float(
                                stationary[idx]
                            )
                        )
                    )

            # ---------- VQNN ----------
            if vqnn_enabled:
                node_context.reliability_score = self._clamp(
                    self._safe_float(
                        self._lookup_by_node(
                            predictions,
                            normalized_node,
                            0.0,
                        )
                    )
                )

                embedding = self._lookup_by_node(
                    embeddings,
                    normalized_node,
                    np.array([]),
                )
                node_context.embedding = np.nan_to_num(
                    np.asarray(
                        embedding,
                        dtype=float,
                    ).reshape(-1),
                    nan=0.0,
                    posinf=0.0,
                    neginf=0.0,
                )

            metrics = self._lookup_by_node(
                repository_metrics,
                normalized_node,
                {},
            )
            if not isinstance(metrics, dict):
                metrics = {}

            centrality = self._clamp(
                self._safe_float(
                    metrics.get(
                        "centrality",
                        0.0,
                    )
                )
            )

            pagerank = self._clamp(
                self._safe_float(
                    metrics.get(
                        "pagerank",
                        0.0,
                    )
                )
            )

            fan_out = self._safe_float(
                metrics.get(
                    "fan_out",
                    0.0,
                )
            )

            if node_context.risk_energy == 0.0:
                node_context.risk_energy = self._clamp(
                    0.60 * centrality
                    + 0.40 * pagerank
                )

            if node_context.qaoa_priority == 0.0:
                node_context.qaoa_priority = self._clamp(
                    0.50 * centrality
                    + 0.25 * pagerank
                    + 0.25 * min(
                        fan_out / 10.0,
                        1.0,
                    )
                )

            if node_context.reliability_score == 0.0:
                node_context.reliability_score = self._clamp(
                    1.0 - node_context.risk_energy
                )

            # ---------- Repo Influence and Uncertainty ----------
            if quantum_walk_enabled:
                node_context.repo_influence = (
                    self._clamp(
                        0.40
                        * node_context.stationary_probability
                        + 0.35
                        * node_context.propagation_score
                        + 0.25
                        * node_context.qaoa_priority
                    )
                )
            else:
                node_context.repo_influence = (
                    self._clamp(
                        0.60 * centrality
                        + 0.40 * pagerank
                    )
                )

            if node_context.reliability_score > 0:
                node_context.uncertainty_score = self._clamp(
                    abs(
                        node_context.qaoa_priority
                        - node_context.reliability_score
                    )
                )
            else:
                node_context.uncertainty_score = self._clamp(
                    abs(
                        node_context.risk_energy
                        - node_context.qaoa_priority
                    )
                )

            node_context.quantum_confidence = self._clamp(
                (
                    0.40
                    * node_context.qsvm_confidence
                    + 0.35
                    * (
                        1.0
                        - node_context.uncertainty_score
                    )
                    + 0.25
                    * node_context.repo_influence
                )
            )

            quantum_modules = []
            if node_context.qaoa_priority > 0.0:
                quantum_modules.append("qaoa")
            if (
                node_context.qsvm_classification
                != "UNKNOWN"
                or node_context.qsvm_confidence > 0.0
            ):
                quantum_modules.append("qsvm")
            if (
                node_context.stationary_probability > 0.0
                or node_context.propagation_score > 0.0
            ):
                quantum_modules.append(
                    "quantum_walk"
                )
            if (
                node_context.embedding.size > 0
                or node_context.reliability_score > 0.0
            ):
                quantum_modules.append("vqnn")

            # ---------- Explainability Metadata ----------
            node_context.metadata.update({
                "quantum_ready": True,
                "has_qaoa": (
                    "qaoa" in quantum_modules
                ),
                "has_qsvm": (
                    "qsvm" in quantum_modules
                ),
                "has_quantum_walk": (
                    "quantum_walk"
                    in quantum_modules
                ),
                "has_vqnn": (
                    "vqnn" in quantum_modules
                ),
                "quantum_modules": quantum_modules,
                "quantum_confidence": (
                    node_context.quantum_confidence
                ),
                "repo_influence": node_context.repo_influence,
                "uncertainty_score": node_context.uncertainty_score,
                "stationary_probability": (
                    node_context.stationary_probability
                ),
                "propagation_score": (
                    node_context.propagation_score
                ),
                "risk_energy": node_context.risk_energy,
                "qaoa_priority": node_context.qaoa_priority,
                "qsvm_confidence": (
                    node_context.qsvm_confidence
                ),
                "reliability_score": (
                    node_context.reliability_score
                ),
                "node": node,
                "qsvm_classification": (
                    node_context.qsvm_classification
                ),
                "embedding_dimension": int(
                    node_context.embedding.size
                ),
            })

            node_context.metadata["summary"] = (
                f"risk={node_context.risk_energy:.3f}, "
                f"priority={node_context.qaoa_priority:.3f}, "
                f"reliability={node_context.reliability_score:.3f}, "
                f"confidence={node_context.quantum_confidence:.3f}"
            )
            node_context.metadata[
                "metrics_available"
            ] = bool(metrics)

            if (
                node_context.embedding.size == 0
                and metrics
            ):
                node_context.embedding = np.nan_to_num(
                    np.asarray(
                        [
                            centrality,
                            pagerank,
                            min(
                                fan_out / 10.0,
                                1.0,
                            ),
                            node_context.risk_energy,
                            node_context.qaoa_priority,
                            node_context.repo_influence,
                        ],
                        dtype=float,
                    ),
                    nan=0.0,
                    posinf=0.0,
                    neginf=0.0,
                )
                node_context.metadata[
                    "embedding_dimension"
                ] = int(
                    node_context.embedding.size
                )

            node_context.metadata[
                "normalized_node"
            ] = normalized_node
            node_context.metadata[
                "repository_metrics_found"
            ] = bool(metrics)

            node_context.metadata[
                "repository_metrics_keys"
            ] = sorted(
                metrics.keys()
            ) if isinstance(
                metrics,
                dict,
            ) else []

            node_context.metadata[
                "embedding_generated"
            ] = (
                node_context.embedding.size > 0
            )

            node_context.metadata[
                "stationary_index_found"
            ] = idx is not None if quantum_walk_enabled else False

            node_context.metadata["debug"] = {
                "qaoa_found": (
                    node_context.qaoa_priority > 0.0
                ),
                "qsvm_found": (
                    node_context.qsvm_classification != "UNKNOWN"
                    or node_context.qsvm_confidence > 0.0
                ),
                "walk_found": (
                    node_context.stationary_probability > 0.0
                    or node_context.propagation_score > 0.0
                ),
                "embedding_found": (
                    node_context.embedding.size > 0
                ),
                "metrics_found": bool(metrics),
                "stationary_index_found": (
                    idx is not None
                ),
            }

            self.context.add_node(node_context)

        self.context.metadata[
            "repository_node_count"
        ] = len(repository_nodes)
        self.context.metadata[
            "quantum_node_count"
        ] = len(self.context.nodes)
        self.context.metadata[
            "qaoa_enabled"
        ] = qaoa_enabled
        self.context.metadata[
            "qsvm_enabled"
        ] = qsvm_enabled
        self.context.metadata[
            "quantum_walk_enabled"
        ] = quantum_walk_enabled
        self.context.metadata[
            "vqnn_enabled"
        ] = vqnn_enabled
        self.context.metadata["quantum_nodes_populated"] = sum(
            1
            for node_ctx in self.context.nodes.values()
            if node_ctx.metadata.get(
                "debug",
                {},
            ).get("qaoa_found")
            or node_ctx.metadata.get(
                "debug",
                {},
            ).get("qsvm_found")
            or node_ctx.metadata.get(
                "debug",
                {},
            ).get("walk_found")
            or node_ctx.metadata.get(
                "debug",
                {},
            ).get("embedding_found")
        )
        return self.context

    def get_node(
        self,
        node: str,
    ) -> Optional[QuantumNodeContext]:
        return self.context.get_node(node)

    def summary(self):
        return self.context.summary()