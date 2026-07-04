

"""
QUEST: Quantum Evaluation of Software Trust

Phase 2:
Trust Representation Engine

Module:
Trust Vector Generator

Purpose:
Constructs the mathematical QUEST Trust Vector representation.

Each software component is transformed into:

T = [C, D, S, R]

where:
C = Complexity Factor
D = Dependency Influence Factor
S = Security Risk Factor
R = Reliability Factor

This vector becomes the direct input representation for
Quantum Feature Encoding, QSVM, QAOA, and QVNN models.
"""


import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List


@dataclass
class TrustVector:
    file_path: str
    vector: List[float]
    trust_score: float
    trust_category: str


class TrustVectorBuilder:
    """
    Converts normalized trust features into
    mathematical vector representations.
    """

    def build_vector(
        self,
        feature: dict
    ) -> TrustVector:

        complexity = feature.get(
            "complexity",
            0
        )

        dependency = feature.get(
            "dependency_influence",
            0
        )

        security = feature.get(
            "security_risk",
            0
        )

        reliability = feature.get(
            "reliability",
            0
        )


        vector = [
            complexity,
            dependency,
            security,
            reliability
        ]


        score = self.calculate_trust_score(
            complexity,
            dependency,
            security,
            reliability
        )


        return TrustVector(
            file_path=feature.get(
                "file_path"
            ),
            vector=vector,
            trust_score=score,
            trust_category=self.classify(score)
        )


    def calculate_trust_score(
        self,
        complexity: float,
        dependency: float,
        security: float,
        reliability: float
    ) -> float:
        """
        Calculates composite QUEST trust score.

        Higher reliability increases trust.
        Higher complexity/security/dependency risks reduce trust.
        """

        risk_component = (
            complexity * 0.3
            + dependency * 0.2
            + security * 0.3
        )

        trust = (
            reliability * 0.5
            + (1 - risk_component) * 0.5
        )

        return round(
            max(min(trust, 1), 0),
            5
        )


    def classify(
        self,
        score: float
    ) -> str:

        if score >= 0.8:
            return "HIGH_TRUST"

        if score >= 0.5:
            return "MODERATE_TRUST"

        return "LOW_TRUST"


    def build_from_file(
        self,
        feature_path: str
    ) -> List[TrustVector]:

        path = Path(feature_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Trust feature file missing: {path}"
            )

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:
            features = json.load(file)


        vectors = [
            self.build_vector(feature)
            for feature in features
        ]

        return vectors


    def save_vectors(
        self,
        vectors: List[TrustVector],
        output_path: str
    ):

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                [asdict(vector) for vector in vectors],
                file,
                indent=4
            )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="QUEST Trust Vector Builder"
    )

    parser.add_argument(
        "--input",
        required=True,
        help="trust_features.json path"
    )

    parser.add_argument(
        "--output",
        default="outputs/trust_vectors.json"
    )

    args = parser.parse_args()


    builder = TrustVectorBuilder()

    vectors = builder.build_from_file(
        args.input
    )

    builder.save_vectors(
        vectors,
        args.output
    )


    print(
        f"Generated {len(vectors)} QUEST Trust Vectors"
    )