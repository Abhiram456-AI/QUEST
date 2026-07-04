

"""
QUEST: Quantum Evaluation of Software Trust

Phase 2:
Trust Representation Engine

Module:
Feature Normalizer

Purpose:
Transforms heterogeneous software engineering measurements into
bounded numerical feature spaces suitable for trust representation
and quantum feature encoding.

Raw metrics such as LOC, complexity, graph density, and reliability
scores are converted into normalized values.
"""


import json
from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class NormalizedMetrics:
    complexity: float
    dependency_influence: float
    security_risk: float
    reliability: float


class TrustFeatureNormalizer:
    """
    Converts raw repository intelligence metrics
    into normalized trust feature components.

    Output range:
        0.0 <= value <= 1.0
    """


    def normalize(
        self,
        metrics: Dict,
        graph_metrics: Dict
    ) -> NormalizedMetrics:

        complexity = self._normalize_complexity(
            metrics.get(
                "cyclomatic_complexity",
                0
            )
        )

        dependency = self._normalize_dependency(
            graph_metrics
        )

        security = self._normalize_security(
            metrics.get(
                "risk_score",
                0
            )
        )

        reliability = self._normalize_reliability(
            metrics.get(
                "maintainability_score",
                100
            )
        )

        return NormalizedMetrics(
            complexity=complexity,
            dependency_influence=dependency,
            security_risk=security,
            reliability=reliability
        )


    def _normalize_complexity(
        self,
        value: float
    ) -> float:
        """
        Normalizes cyclomatic complexity.

        Complexity above 50 is considered highly risky
        and saturated.
        """

        return round(
            min(value / 50, 1.0),
            5
        )


    def _normalize_dependency(
        self,
        graph_metrics: Dict
    ) -> float:
        """
        Converts graph connectivity into dependency influence.
        """

        density = graph_metrics.get(
            "density",
            0
        )

        degree = graph_metrics.get(
            "average_degree",
            0
        )

        dependency_score = (
            density * 0.6
            + min(degree / 20, 1) * 0.4
        )

        return round(
            min(dependency_score, 1),
            5
        )


    def _normalize_security(
        self,
        risk: float
    ) -> float:
        """
        Security risk values are already produced
        in normalized form by Phase 1 metrics.
        """

        return round(
            min(max(risk, 0), 1),
            5
        )


    def _normalize_reliability(
        self,
        maintainability: float
    ) -> float:
        """
        Converts maintainability score into reliability factor.
        """

        return round(
            min(max(maintainability / 100, 0), 1),
            5
        )


if __name__ == "__main__":

    sample_metrics = {
        "cyclomatic_complexity": 20,
        "maintainability_score": 75,
        "risk_score": 0.3
    }

    sample_graph = {
        "density": 0.2,
        "average_degree": 4
    }

    normalizer = TrustFeatureNormalizer()

    result = normalizer.normalize(
        sample_metrics,
        sample_graph
    )

    print(
        json.dumps(
            asdict(result),
            indent=4
        )
    )