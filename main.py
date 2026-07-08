

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

from quest.quantum.qsvm_classifier import QUESTQSVMClassifier
from quest.quantum.quantum_walk import QuantumWalkEngine
from quest.quantum.qaoa_optimizer import QUESTQAOAOptimizer
from quest.quantum.qvnn_predictor import QUESTQVNNPredictor

from quest.agents.agent_orchestrator import AgentOrchestrator
from quest.retrieval.document_loader import DocumentLoader
from quest.retrieval.evidence_indexer import EvidenceIndexer
from quest.retrieval.quest_assistant import QUESTAssistant


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


    def execute_phase_three(self):
        """
        Runs the complete Quantum Trust Intelligence Engine.

        Executes:
        - QSVM Trust Classification
        - Quantum Walk Risk Propagation
        - QAOA Reliability Optimization
        - QVNN Reliability Prediction
        """

        print("QUEST Phase 3 Started")


        quantum_output = (
            Path(OUTPUT_DIR)
            / "quantum_results"
        )

        quantum_output.mkdir(
            parents=True,
            exist_ok=True
        )


        qsvm = QUESTQSVMClassifier()

        qsvm_result = qsvm.train_and_evaluate(
            "datasets/X.npy",
            "datasets/y.npy"
        )

        qsvm.save_results(
            qsvm_result,
            str(quantum_output / "qsvm_results.json")
        )

        print("QSVM Trust Classification Completed")


        quantum_walk = QuantumWalkEngine()

        quantum_walk.analyze_repository(
            str(Path(OUTPUT_DIR) / "repository_intelligence.json"),
            str(quantum_output / "quantum_walk_results.json")
        )

        print("Quantum Walk Risk Propagation Completed")


        qaoa = QUESTQAOAOptimizer()

        qaoa_results = qaoa.optimize(
            str(Path(OUTPUT_DIR) / "trust_vectors.json"),
            str(quantum_output / "quantum_walk_results.json")
        )

        qaoa.save_results(
            qaoa_results,
            str(quantum_output / "qaoa_results.json")
        )

        print("QAOA Reliability Optimization Completed")


        qvnn = QUESTQVNNPredictor()

        qvnn_results = qvnn.predict(
            "datasets/X.npy"
        )

        qvnn.save_results(
            qvnn_results,
            str(quantum_output / "qvnn_results.json")
        )

        print("QVNN Reliability Prediction Completed")

        print("QUEST Phase 3 Completed")


    def execute_phase_four(self):
        """
        Runs the complete Autonomous Multi-Agent Verification Framework.

        Executes:
        - Reviewer Agent
        - Security Agent
        - Quantum Agent
        - Critic Agent
        - Verifier Agent
        - Explainer Agent
        """

        print("QUEST Phase 4 Started")

        orchestrator = AgentOrchestrator()

        verification_results = orchestrator.execute()

        orchestrator.save_results(
            verification_results
        )

        print(
            "QUEST Autonomous Agent Verification Completed"
        )

        print("QUEST Phase 4 Completed")

        return verification_results


    def execute_phase_five(self):
        """
        Runs the complete Context Retrieval & Query Intelligence preparation.

        Executes:
        - QUEST Document Loading
        - Evidence Index Construction

        Enables:
        - Query Router
        - Context Builder
        - QUEST Assistant
        """

        print("QUEST Phase 5 Started")

        loader = DocumentLoader()

        documents = loader.load_documents()

        loader.export_documents()

        print(
            f"QUEST Knowledge Documents Loaded: {len(documents)}"
        )

        indexer = EvidenceIndexer()

        evidence = indexer.build_index()

        indexer.save_index()

        print(
            f"QUEST Evidence Index Generated: {len(evidence)} chunks"
        )

        print("QUEST Phase 5 Completed")

        return evidence

    def execute_phase_six(self):
        """
        Runs the complete Autonomous Decision Intelligence engine (Phase 6).
        """
        print("QUEST Phase 6 Started")

        from quest.decision.decision_engine import DecisionEngine
        engine = DecisionEngine(OUTPUT_DIR)
        report = engine.execute_decision_pipeline()

        print("QUEST Phase 6 Completed")
        return report



def main():

    parser = argparse.ArgumentParser(
        description="QUEST Research Framework"
    )

    parser.add_argument(
        "--repo",
        required=True,
        help="Repository path for analysis"
    )

    parser.add_argument(
        "--chat",
        action="store_true",
        help="Start QUEST interactive assistant after analysis"
    )

    args = parser.parse_args()

    engine = QUESTEngine(
        args.repo
    )

    engine.execute_phase_one()
    engine.execute_phase_two()
    engine.execute_phase_three()
    engine.execute_phase_four()
    engine.execute_phase_five()
    engine.execute_phase_six()

    # Save reproducibility and version info
    version_info = {
        "quest_version": "6.0.0-calibrated",
        "phase_version": "Phase 6: Decision Intelligence",
        "algorithms": {
            "QSVM": "Fidelity Quantum Kernel Classification",
            "CTQW": "Continuous-Time Quantum Walk Risk Propagation",
            "QAOA": "Quantum Approximate Optimization Algorithm Reliability Prioritization",
            "QVNN": "Variational Quantum Neural Network Reliability Regression"
        },
        "configuration_hash": "a4d8c6b29f03d528f8c9c0b11e2f3d4a"
    }
    version_file = Path(OUTPUT_DIR) / "version_info.json"
    version_file.parent.mkdir(parents=True, exist_ok=True)
    with open(version_file, "w") as f:
        json.dump(version_info, f, indent=4)

    if args.chat:
        assistant = QUESTAssistant()
        assistant.start()


if __name__ == "__main__":
    main()