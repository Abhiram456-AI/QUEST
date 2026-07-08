"""
QUEST: Quantum Evaluation of Software Trust

Phase 5:
Context Retrieval & Query Intelligence Engine

Module:
Evidence Indexer

Purpose:
Transforms loaded QUEST documents into searchable evidence units.

Converts:
Raw JSON Intelligence
        ↓
Structured Evidence Memory
        ↓
Retrieval-ready Knowledge Base
"""


import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Any, Dict, List

from quest.retrieval.document_loader import DocumentLoader


@dataclass
class EvidenceChunk:
    """
    Semantic QUEST evidence unit.
    """

    evidence_id: str
    source: str
    category: str
    component: str
    intent_tags: List[str]
    content: str
    metadata: Dict


class EvidenceIndexer:
    """
    Builds searchable evidence memory from QUEST documents.
    """

    def __init__(self):
        self.evidence_store: List[EvidenceChunk] = []


    def build_index(self) -> List[EvidenceChunk]:
        """
        Converts all QUEST documents into evidence chunks.
        """

        loader = DocumentLoader()

        documents = loader.load_documents()

        counter = 0


        for document in documents:

            content = document.content
            source = document.source
            category = document.category
            phase = document.metadata.get(
                "phase",
                "UNKNOWN"
            )

            # Special case: unpack files in repository_intelligence individually
            if source == "repository_intelligence" and isinstance(content, dict) and "files" in content:
                # Add repository global metadata first
                repo_meta = {k: v for k, v in content.items() if k != "files"}
                self.add_chunk(counter, source, category, phase, repo_meta)
                counter += 1
                
                # Add each file report individually
                for file_report in content["files"]:
                    self.add_chunk(counter, source, category, phase, file_report)
                    counter += 1

            # Special case: unpack agent findings individually
            elif source == "agent_verification" and isinstance(content, dict):
                for agent_name, findings in content.items():
                    if isinstance(findings, list):
                        for finding in findings:
                            # Attach agent_name to the finding dict
                            finding_copy = dict(finding)
                            finding_copy["agent_name"] = agent_name
                            self.add_chunk(counter, source, category, phase, finding_copy)
                            counter += 1
                    else:
                        self.add_chunk(counter, source, category, phase, {agent_name: findings})
                        counter += 1

            elif isinstance(content, list):

                for item in content:

                    self.add_chunk(
                        counter,
                        source,
                        category,
                        phase,
                        item
                    )

                    counter += 1


            elif isinstance(content, dict):

                for key, value in content.items():

                    self.add_chunk(
                        counter,
                        source,
                        category,
                        phase,
                        {
                            key: value
                        }
                    )

                    counter += 1


        return self.evidence_store



    def add_chunk(
        self,
        index: int,
        source: str,
        category: str,
        phase: str,
        data: Any
    ):
        """
        Creates one semantic evidence entry.
        """

        component = self.extract_component(data)

        chunk = EvidenceChunk(
            evidence_id=f"EV-{index}",
            source=source,
            category=category,
            component=component,
            intent_tags=self.generate_tags(
                source,
                category
            ),
            content=json.dumps(
                data,
                default=str
            ),
            metadata={
                "phase": phase,
                "length": len(str(data)),
                "importance": self.calculate_importance(
                    category
                )
            }
        )

        self.evidence_store.append(chunk)


    def extract_component(
        self,
        data: Any
    ) -> str:
        """
        Attempts to identify related software component.
        """

        if isinstance(data, dict):

            possible_keys = [
                "component",
                "file",
                "file_path",
                "path",
                "source_component"
            ]

            for key in possible_keys:

                if key in data:
                    return str(
                        data[key]
                    )


        return "repository"


    def generate_tags(
        self,
        source: str,
        category: str
    ) -> List[str]:
        """
        Generates retrieval intent tags.
        """

        tags = [category]

        if category == "quantum":
            tags.extend([
                "risk",
                "trace",
                "optimization"
            ])

        if category == "trust":
            tags.extend([
                "risk",
                "comparison",
                "reliability"
            ])

        if category == "agent":
            tags.extend([
                "verification",
                "decision",
                "trace"
            ])

        if category == "repository":
            tags.extend([
                "architecture",
                "component"
            ])

        tags.append(source)

        return tags


    def calculate_importance(
        self,
        category: str
    ) -> float:
        """
        Assigns evidence ranking importance.
        """

        weights = {
            "agent": 0.9,
            "quantum": 0.85,
            "trust": 0.8,
            "repository": 0.7
        }

        return weights.get(
            category,
            0.5
        )


    def save_index(
        self,
        output_path="outputs/evidence_index.json"
    ):
        """
        Saves QUEST evidence memory.
        """

        output = Path(
            output_path
        )

        output.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            output,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                [
                    asdict(chunk)
                    for chunk in self.evidence_store
                ],
                file,
                indent=4
            )


if __name__ == "__main__":

    indexer = EvidenceIndexer()

    evidence = indexer.build_index()

    indexer.save_index()

    print(
        f"Indexed {len(evidence)} QUEST evidence chunks"
    )
