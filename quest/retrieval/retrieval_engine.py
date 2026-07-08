"""
QUEST: Quantum Evaluation of Software Trust

Phase 5:
Context Retrieval & Query Intelligence Engine

Module:
Retrieval Engine

Purpose:
Retrieves the most relevant QUEST evidence chunks for a user query.

Uses:
- Component matching
- Keyword relevance scoring
- Source-aware retrieval
"""


import json
from pathlib import Path
from typing import Dict, List

from quest.retrieval.evidence_indexer import EvidenceIndexer
from quest.retrieval.query_router import QueryRouter


class RetrievalEngine:
    """
    Searches QUEST evidence memory and retrieves relevant knowledge.
    """

    def __init__(
        self,
        index_path: str = "outputs/evidence_index.json"
    ):

        self.index_path = Path(index_path)

        self.evidence = self.load_or_create_index()

        self.router = QueryRouter()


    def load_or_create_index(
        self
    ) -> List[Dict]:
        """
        Loads evidence index or creates it if missing.
        """

        if self.index_path.exists():

            with open(
                self.index_path,
                "r",
                encoding="utf-8"
            ) as file:

                return json.load(file)


        indexer = EvidenceIndexer()

        evidence = indexer.build_index()

        indexer.save_index()

        return [
            item.__dict__
            for item in evidence
        ]


    def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Retrieves intent-aware and evidence-grounded QUEST knowledge.
        """

        intent = self.router.route(query)

        query_terms = self.normalize(query)

        mentioned_component = self.extract_component_query(
            query_terms
        )

        if mentioned_component:

            if not self.component_exists(
                mentioned_component
            ):

                return []

        scored_results = []

        for item in self.evidence:

            if item.get("source") not in intent.target_sources:
                continue

            # Strict cross-component filtering:
            # If the user mentioned a specific component, filter out all other specific components.
            if mentioned_component:
                comp_lower = item.get("component", "").lower()
                clean_mentioned = mentioned_component.replace("file:", "").lower()
                if comp_lower != "repository" and clean_mentioned not in comp_lower:
                    continue

            score = self.calculate_score(
                query_terms,
                item
            )

            score += item.get(
                "metadata",
                {}
            ).get(
                "importance",
                0
            )

            if score > 0:

                scored_results.append(
                    (
                        score,
                        item
                    )
                )


        scored_results.sort(
            key=lambda value: value[0],
            reverse=True
        )

        return [
            result
            for _, result in scored_results[:top_k]
        ]


    def calculate_score(
        self,
        query_terms: List[str],
        evidence: Dict
    ) -> float:
        """
        Calculates semantic evidence relevance.
        """

        searchable_text = (
            evidence.get("component", "")
            + " "
            + evidence.get("source", "")
            + " "
            + " ".join(
                evidence.get(
                    "intent_tags",
                    []
                )
            )
            + " "
            + str(evidence.get("content", ""))
        ).lower()

        score = 0

        for term in query_terms:
            if term in searchable_text:
                score += 1

        component = evidence.get(
            "component",
            ""
        ).lower()

        for term in query_terms:
            if term in component:
                score += 3

        # Source Match Boost: heavily prioritize chunks from the requested data layer/source
        source_name = evidence.get("source", "").lower()
        for term in query_terms:
            if term == source_name or term in source_name.replace("_", " "):
                score += 5.0

        # Component Disambiguation:
        # Determine if query asks for a test or implementation
        query_has_test = any("test" in t for t in query_terms)
        comp_is_test = "test" in component or "tests/" in component

        if comp_is_test:
            if query_has_test:
                score += 2
            else:
                score -= 3
        else:
            if not query_has_test:
                score += 2

        return score



    def extract_component_query(
        self,
        query_terms: List[str]
    ):
        """
        Extracts file/component references from user queries.
        """

        for term in query_terms:

            if ".py" in term:
                # Strip leading and trailing punctuation (e.g. question marks)
                return term.strip("?.!,;:'\"()")


        return None


    def component_exists(
        self,
        component: str
    ) -> bool:
        """
        Checks whether QUEST has evidence for a component.
        """

        for item in self.evidence:

            if component in item.get(
                "component",
                ""
            ).lower():

                return True

        return False


    def normalize(
        self,
        text: str
    ) -> List[str]:
        """
        Simple query normalization.
        """

        return [
            token.strip().lower()
            for token in text.split()
            if len(token.strip()) > 2
        ]


if __name__ == "__main__":

    engine = RetrievalEngine()

    query = "Why is repository_scanner.py risky"

    results = engine.retrieve(
        query
    )

    print(
        f"Retrieved {len(results)} evidence chunks"
    )

    for item in results:
        print(
            item["source"],
            "->",
            item["component"]
        )
