"""
QUEST: Quantum Evaluation of Software Trust

Phase 5:
Context Retrieval & Query Intelligence Engine

Module:
Document Loader

Purpose:
Loads all generated QUEST intelligence artifacts and converts them
into a unified knowledge source for retrieval and questioning.

Sources:
- Repository Intelligence
- Trust Representation
- Quantum Intelligence
- Autonomous Agent Verification
"""


import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Any, Dict, List


@dataclass
class QUESTDocument:
    """
    Structured QUEST knowledge document.
    """

    document_id: str
    source: str
    category: str
    content: Any
    metadata: Dict


class DocumentLoader:
    """
    Loads all QUEST-generated artifacts into a unified memory layer.
    """

    def __init__(
        self,
        output_directory: str = "outputs"
    ):

        self.output_directory = Path(
            output_directory
        )


    def load_json(
        self,
        path: Path
    ):
        """
        Safely loads JSON artifacts.
        """

        if not path.exists():
            return None

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)


    def load_documents(
        self
    ) -> List[QUESTDocument]:
        """
        Loads every QUEST phase output.
        """

        documents = []

        artifact_paths = {
            "repository_intelligence": (
                self.output_directory
                / "repository_intelligence.json"
            ),

            "trust_vectors": (
                self.output_directory
                / "trust_vectors.json"
            ),

            "qsvm_results": (
                self.output_directory
                / "quantum_results"
                / "qsvm_results.json"
            ),

            "quantum_walk_results": (
                self.output_directory
                / "quantum_results"
                / "quantum_walk_results.json"
            ),

            "qaoa_results": (
                self.output_directory
                / "quantum_results"
                / "qaoa_results.json"
            ),

            "qvnn_results": (
                self.output_directory
                / "quantum_results"
                / "qvnn_results.json"
            ),

            "agent_verification": (
                self.output_directory
                / "agent_results"
                / "verification_results.json"
            )
        }


        for source, path in artifact_paths.items():

            data = self.load_json(
                path
            )

            if data is None:
                continue

            documents.append(
                QUESTDocument(
                    document_id=f"DOC-{len(documents)}",
                    source=source,
                    category=self.detect_category(source),
                    content=data,
                    metadata={
                        "path": str(path),
                        "phase": self.detect_phase(source),
                        "artifact": source,
                        "available": True
                    }
                )
            )


        return documents


    def detect_phase(
        self,
        source: str
    ) -> str:
        """
        Maps artifacts back to QUEST phases.
        """

        if source == "repository_intelligence":
            return "PHASE_1"

        if source == "trust_vectors":
            return "PHASE_2"

        if source in [
            "qsvm_results",
            "quantum_walk_results",
            "qaoa_results",
            "qvnn_results"
        ]:
            return "PHASE_3"

        if source == "agent_verification":
            return "PHASE_4"

        return "UNKNOWN"


    def detect_category(
        self,
        source: str
    ) -> str:
        """
        Maps artifacts into reasoning categories.
        """

        if source == "repository_intelligence":
            return "repository"

        if source == "trust_vectors":
            return "trust"

        if source in [
            "qsvm_results",
            "quantum_walk_results",
            "qaoa_results",
            "qvnn_results"
        ]:
            return "quantum"

        if source == "agent_verification":
            return "agent"

        return "unknown"


    def export_documents(
        self,
        output_path="outputs/retrieval_documents.json"
    ):
        """
        Saves loaded documents for inspection/debugging.
        """

        documents = self.load_documents()

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                [asdict(doc) for doc in documents],
                file,
                indent=4
            )


if __name__ == "__main__":

    loader = DocumentLoader()

    docs = loader.load_documents()

    loader.export_documents()

    print(
        f"Loaded {len(docs)} QUEST knowledge documents"
    )

    for doc in docs:
        print(
            doc.document_id,
            doc.source,
            doc.category,
            doc.metadata["phase"]
        )