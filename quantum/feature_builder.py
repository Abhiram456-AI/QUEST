"""
Quantum feature construction for QTrustCode.

Converts repository metrics into:
1. Raw feature matrix
2. Dynamically normalized feature matrix
3. Unit-length amplitude vectors suitable for quantum models

This module serves as the data preparation layer for:
    - QSVM
    - QVNN
    - Quantum Walk Engine
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np


class QuantumFeatureBuilder:
    """
    Build repository feature vectors for quantum algorithms.
    """

    FEATURE_NAMES = [
        "risk_score",
        "fan_in",
        "fan_out",
        "centrality",
        "pagerank",
        "blast_radius",
        "instability",
        "semantic_risk",
        "repository_influence",
        "propagation_risk",
    ]

    def __init__(self, epsilon: float = 1e-9):
        self.epsilon = max(float(epsilon), 1e-12)

    def _extract_feature_vector(
        self,
        metadata: Dict,
    ) -> List[float]:
        """
        Extract a consistent feature vector from node metadata.
        Missing values safely default to zero.
        """

        risk_score = float(metadata.get("risk_score", 0.0))
        centrality = float(metadata.get("centrality", 0.0))
        pagerank = float(metadata.get("pagerank", 0.0))
        blast_radius = float(metadata.get("blast_radius", 0.0))

        repository_influence = (
            centrality * pagerank
        )

        propagation_risk = (
            risk_score * blast_radius
        )

        return [
            risk_score,
            float(metadata.get("fan_in", 0.0)),
            float(metadata.get("fan_out", 0.0)),
            centrality,
            pagerank,
            blast_radius,
            float(metadata.get("instability", 0.0)),
            float(metadata.get("semantic_risk", 0.0)),
            repository_influence,
            propagation_risk,
        ]

    def _normalize(
        self,
        matrix: np.ndarray,
    ) -> np.ndarray:
        """
        Dynamic feature-wise min-max normalization.
        """

        if matrix.size == 0:
            return matrix

        mins = matrix.min(axis=0)
        maxs = matrix.max(axis=0)
        ranges = np.maximum(maxs - mins, self.epsilon)

        normalized = (matrix - mins) / ranges
        normalized = np.nan_to_num(
            normalized,
            nan=0.0,
            posinf=1.0,
            neginf=0.0,
        )
        return np.clip(normalized, 0.0, 1.0)

    def _amplitude_encode(
        self,
        matrix: np.ndarray,
    ) -> np.ndarray:
        """
        Convert normalized feature vectors into unit-length
        amplitude vectors.
        """

        if matrix.size == 0:
            return matrix

        amplitudes = []

        for row in matrix:
            norm = float(np.linalg.norm(row))

            if norm <= self.epsilon:
                amplitudes.append(
                    np.full_like(
                        row,
                        1.0 / np.sqrt(len(row)),
                    )
                )
            else:
                amplitudes.append(row / norm)

        return np.asarray(amplitudes, dtype=float)

    def build(
        self,
        repository_metrics: Dict[str, Dict],
    ) -> Dict:
        """
        Build quantum-ready repository features.
        """

        if not repository_metrics:
            return {
                "modules": [],
                "feature_names": self.FEATURE_NAMES,
                "num_modules": 0,
                "num_features": len(self.FEATURE_NAMES),
                "amplitude_dimension": len(self.FEATURE_NAMES),
                "feature_matrix": [],
                "normalized_matrix": [],
                "amplitude_vectors": [],
            }

        modules = sorted(repository_metrics.keys())

        feature_rows = [
            self._extract_feature_vector(
                repository_metrics[module]
            )
            for module in modules
        ]

        feature_matrix = np.asarray(
            feature_rows,
            dtype=float,
        )

        normalized_matrix = self._normalize(
            feature_matrix
        )

        amplitude_vectors = self._amplitude_encode(
            normalized_matrix
        )

        return {
            "modules": modules,
            "feature_names": self.FEATURE_NAMES,
            "num_modules": len(modules),
            "num_features": len(self.FEATURE_NAMES),
            "amplitude_dimension": len(self.FEATURE_NAMES),
            "feature_statistics": {
                "mins": feature_matrix.min(axis=0).round(6).tolist(),
                "maxs": feature_matrix.max(axis=0).round(6).tolist(),
                "means": feature_matrix.mean(axis=0).round(6).tolist(),
            },
            "feature_matrix": feature_matrix.round(6).tolist(),
            "normalized_matrix": normalized_matrix.round(6).tolist(),
            "amplitude_vectors": amplitude_vectors.round(6).tolist(),
        }