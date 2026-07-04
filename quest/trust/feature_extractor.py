

"""
QUEST: Quantum Evaluation of Software Trust

Phase 2:
Trust Representation Engine

Module:
Trust Feature Extractor

Purpose:
Consumes Repository Intelligence Reports generated from Phase 1
and transforms raw software analysis data into normalized trust
feature representations.

This module creates the classical feature foundation required before
quantum feature encoding.
"""


import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict

from quest.trust.normalizer import TrustFeatureNormalizer


@dataclass
class TrustFeature:
    file_path: str
    complexity: float
    dependency_influence: float
    security_risk: float
    reliability: float


class TrustFeatureExtractor:
    """
    Converts repository intelligence artifacts into
    normalized software trust features.
    """

    def __init__(self):
        self.normalizer = TrustFeatureNormalizer()


    def extract(
        self,
        intelligence_report_path: str
    ) -> List[TrustFeature]:

        report_path = Path(
            intelligence_report_path
        )

        if not report_path.exists():
            raise FileNotFoundError(
                f"Repository intelligence report missing: {report_path}"
            )

        with open(
            report_path,
            "r",
            encoding="utf-8"
        ) as file:

            report = json.load(file)


        extracted_features = []


        for file_entry in report.get("files", []):

            metrics = file_entry.get(
                "metrics"
            )

            graph = file_entry.get(
                "graph",
                {}
            )


            if not metrics:
                continue


            graph_metrics = graph.get(
                "graph_metrics",
                {}
            )


            normalized = self.normalizer.normalize(
                metrics,
                graph_metrics
            )


            feature = TrustFeature(
                file_path=file_entry.get(
                    "file"
                ),

                complexity=normalized.complexity,

                dependency_influence=normalized.dependency_influence,

                security_risk=normalized.security_risk,

                reliability=normalized.reliability
            )


            extracted_features.append(
                feature
            )


        return extracted_features


    def save_features(
        self,
        features: List[TrustFeature],
        output_path: str
    ):

        output = [
            asdict(feature)
            for feature in features
        ]

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                output,
                file,
                indent=4
            )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="QUEST Trust Feature Extractor"
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Repository intelligence JSON path"
    )

    parser.add_argument(
        "--output",
        default="outputs/trust_features.json",
        help="Feature output path"
    )

    args = parser.parse_args()


    extractor = TrustFeatureExtractor()

    features = extractor.extract(
        args.input
    )

    extractor.save_features(
        features,
        args.output
    )


    print(
        f"Generated {len(features)} QUEST trust feature vectors"
    )