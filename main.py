

"""
QUEST: Quantum Evaluation of Software Trust

Main Execution Engine

Purpose:
Acts as the Phase 1 orchestration entry point.

Transforms a raw software repository into a complete
Repository Intelligence Report by executing:

1. Repository Scanner
2. AST Analyzer
3. Dependency Analyzer
4. Call Graph Builder
5. Code Metrics Engine

The generated intelligence artifact becomes the input
for Phase 2: Trust Representation Engine.
"""


import argparse
import json
from pathlib import Path
from dataclasses import asdict


from quest.intelligence.repository_scanner import RepositoryScanner
from quest.intelligence.ast_analyzer import ASTAnalyzer
from quest.intelligence.dependency_analyzer import DependencyAnalyzer
from quest.intelligence.call_graph import CallGraphBuilder
from quest.intelligence.code_metrics import CodeMetricsAnalyzer

from quest.trust.feature_extractor import TrustFeatureExtractor
from quest.trust.trust_vector import TrustVectorBuilder
from quest.trust.dataset_builder import DatasetBuilder


OUTPUT_DIR = "outputs"


class QUESTEngine:
    """
    Central QUEST execution pipeline.
    """

    def __init__(self, repository_path: str):
        self.repository_path = Path(repository_path)

        if not self.repository_path.exists():
            raise FileNotFoundError(
                f"Repository does not exist: {repository_path}"
            )

        Path(OUTPUT_DIR).mkdir(
            exist_ok=True
        )


    def execute_phase_one(self):
        """
        Runs the complete Repository Intelligence Engine.
        """

        print("QUEST Phase 1 Started")


        scanner = RepositoryScanner(
            str(self.repository_path)
        )

        repository_metadata = scanner.scan()


        intelligence_report = {
            "repository": asdict(repository_metadata),
            "files": []
        }


        for file_info in repository_metadata.files:

            file_path = (
                self.repository_path
                / file_info["path"]
            )

            print(
                f"Analyzing: {file_info['path']}"
            )

            file_report = {
                "file": file_info["path"]
            }


            try:
                ast_result = ASTAnalyzer().analyze_file(
                    str(file_path)
                )

                file_report["ast"] = asdict(
                    ast_result
                )

            except Exception as error:
                file_report["ast_error"] = str(error)


            try:
                dependency_result = DependencyAnalyzer().analyze_file(
                    str(file_path)
                )

                file_report["dependencies"] = asdict(
                    dependency_result
                )

            except Exception as error:
                file_report["dependency_error"] = str(error)


            try:
                graph_result = CallGraphBuilder().build_graph(
                    str(file_path)
                )

                file_report["graph"] = asdict(
                    graph_result
                )

            except Exception as error:
                file_report["graph_error"] = str(error)


            try:
                metric_result = CodeMetricsAnalyzer().analyze_file(
                    str(file_path)
                )

                file_report["metrics"] = asdict(
                    metric_result
                )

            except Exception as error:
                file_report["metric_error"] = str(error)


            intelligence_report["files"].append(
                file_report
            )


        output_file = (
            Path(OUTPUT_DIR)
            / "repository_intelligence.json"
        )

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                intelligence_report,
                file,
                indent=4
            )


        print(
            f"QUEST Intelligence Report Generated: {output_file}"
        )

        return intelligence_report


    def execute_phase_two(self):
        """
        Runs the complete Trust Representation Engine.

        Converts Repository Intelligence output into:
        - normalized trust features
        - QUEST Trust Vectors
        - ML/Quantum ready datasets
        """

        print("QUEST Phase 2 Started")

        intelligence_path = (
            Path(OUTPUT_DIR)
            / "repository_intelligence.json"
        )

        trust_features_path = (
            Path(OUTPUT_DIR)
            / "trust_features.json"
        )

        trust_vectors_path = (
            Path(OUTPUT_DIR)
            / "trust_vectors.json"
        )

        dataset_path = (
            Path(OUTPUT_DIR)
            / "quest_dataset.json"
        )


        feature_extractor = TrustFeatureExtractor()

        features = feature_extractor.extract(
            str(intelligence_path)
        )

        feature_extractor.save_features(
            features,
            str(trust_features_path)
        )

        print(
            f"Generated Trust Features: {trust_features_path}"
        )


        vector_builder = TrustVectorBuilder()

        vectors = vector_builder.build_from_file(
            str(trust_features_path)
        )

        vector_builder.save_vectors(
            vectors,
            str(trust_vectors_path)
        )

        print(
            f"Generated Trust Vectors: {trust_vectors_path}"
        )


        dataset_builder = DatasetBuilder()

        dataset = dataset_builder.build(
            str(trust_vectors_path)
        )

        dataset_builder.save_json(
            dataset,
            str(dataset_path)
        )

        dataset_builder.export_numpy(
            dataset,
            "datasets"
        )

        print(
            "QUEST Dataset Generated"
        )

        return dataset



def main():

    parser = argparse.ArgumentParser(
        description="QUEST Research Framework"
    )

    parser.add_argument(
        "--repo",
        required=True,
        help="Repository path for analysis"
    )

    args = parser.parse_args()

    engine = QUESTEngine(
        args.repo
    )

    engine.execute_phase_one()
    engine.execute_phase_two()


if __name__ == "__main__":
    main()