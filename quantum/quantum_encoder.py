"""
Quantum feature encoder for QTrustCode.

This module converts repository risk metrics into normalized feature
vectors that can be consumed by quantum algorithms such as QAOA,
QSVM, quantum walks, and VQNNs.
"""

from __future__ import annotations

from typing import Dict, List


class QuantumEncoder:
    """
    Encodes repository metrics into normalized quantum feature vectors.

    Input:
        {
            "fan_in": 4,
            "fan_out": 5,
            "centrality": 0.7,
            "blast_radius": 6,
            "instability": 0.71
        }

    Output:
        [0.4, 0.5, 0.7, 0.6, 0.71]
    """

    MINIMUM_MAXIMA = {
        "fan_in": 1.0,
        "fan_out": 1.0,
        "centrality": 1.0,
        "blast_radius": 1.0,
        "instability": 1.0,
    }

    FEATURE_ORDER = [
        "fan_in",
        "fan_out",
        "centrality",
        "blast_radius",
        "instability",
    ]

    def __init__(self, maxima: Dict[str, float] | None = None):
        self.maxima = dict(self.MINIMUM_MAXIMA)
        if maxima:
            self.maxima.update(maxima)

    def fit_maxima(self, repository_metrics: Dict[str, Dict]) -> Dict[str, float]:
        """
        Learn maxima dynamically from repository metrics.

        Expected input:
        {
            "module.py": {
                "fan_in": 2,
                "fan_out": 5,
                ...
            }
        }
        """
        if not isinstance(repository_metrics, dict):
            self.maxima = dict(self.MINIMUM_MAXIMA)
            return self.maxima

        maxima = dict(self.MINIMUM_MAXIMA)

        for metrics in repository_metrics.values():
            if not isinstance(metrics, dict):
                continue
            for feature in self.FEATURE_ORDER:
                try:
                    value = float(metrics.get(feature, 0.0) or 0.0)
                except (TypeError, ValueError):
                    value = 0.0
                maxima[feature] = max(maxima[feature], value)

        self.maxima = maxima
        return self.maxima

    def encode_repository(self, repository_metrics: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Dynamically fit maxima and encode every repository node.
        """
        if not isinstance(repository_metrics, dict):
            return {}

        self.fit_maxima(repository_metrics)

        encoded = {}

        for node, metrics in repository_metrics.items():
            if not isinstance(metrics, dict):
                metrics = {}
            encoded[node] = {
                "quantum_features": self.encode(metrics),
                "feature_order": self.FEATURE_ORDER,
            }

        return encoded

    def normalize(self, value: float, maximum: float) -> float:
        """Normalize a metric into the range [0, 1]."""
        if maximum <= 0:
            return 0.0
        return round(min(max(float(value) / maximum, 0.0), 1.0), 3)

    def encode(self, metrics: Dict[str, float]) -> List[float]:
        """Encode repository metrics into an ordered feature vector."""
        if not isinstance(metrics, dict):
            metrics = {}
        vector = []

        for feature in self.FEATURE_ORDER:
            try:
                value = float(metrics.get(feature, 0.0) or 0.0)
            except (TypeError, ValueError):
                value = 0.0
            maximum = self.maxima.get(
                feature,
                self.MINIMUM_MAXIMA[feature]
            )
            vector.append(self.normalize(value, maximum))

        return vector

    def encode_node(self, node_data: Dict) -> Dict:
        """Attach quantum features to a repository node."""
        if not isinstance(node_data, dict):
            node_data = {}
        metrics = node_data.get("metrics", node_data)
        if not isinstance(metrics, dict):
            metrics = {}

        return {
            "node": node_data.get("node"),
            "quantum_features": self.encode(metrics),
            "feature_order": self.FEATURE_ORDER,
        }


encoder = QuantumEncoder()