"""
QUEST: Quantum Evaluation of Software Trust

Phase 5.5:
Reasoning Reliability Upgrade

Module:
Query Router

Purpose:
Classifies user intent before retrieval so QUEST searches the correct
knowledge sources and avoids incorrect evidence selection.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class QueryIntent:
    """
    Represents a routed QUEST query.
    """

    query: str
    intent: str
    target_sources: List[str]
    confidence: float


class QueryRouter:
    """
    Advanced intent router for QUEST reasoning.
    """

    def __init__(self):

        self.intent_keywords = {
            "ARCHITECTURE_QUERY": [
                "architecture",
                "architectural",
                "overview",
                "project",
                "repository",
                "system",
                "pipeline",
                "framework",
                "layout",
                "modules",
                "roles"
            ],

            "COMPONENT_QUERY": [
                "file",
                "files",
                "class",
                "classes",
                "function",
                "functions",
                "module",
                "component",
                "inside"
            ],

            "RISK_QUERY": [
                "why",
                "risk",
                "risky",
                "trust",
                "score",
                "reliable",
                "reliability",
                "quality",
                "complexity"
            ],

            "COMPARISON_QUERY": [
                "compare",
                "difference",
                "better",
                "worse",
                "versus",
                "vs"
            ],

            "QUANTUM_QUERY": [
                "quantum",
                "qsvm",
                "qaoa",
                "qvnn",
                "walk",
                "optimization",
                "prediction"
            ],

            "AGENT_QUERY": [
                "agent",
                "reviewer",
                "security",
                "critic",
                "verifier",
                "verification"
            ],

            "TRACE_QUERY": [
                "trace",
                "chain",
                "flow",
                "cause",
                "caused",
                "evidence",
                "from analysis",
                "final decision"
            ],

            "METHODOLOGY_QUERY": [
                "methodology",
                "novelty",
                "different",
                "traditional",
                "approach",
                "research"
            ],

            "DECISION_QUERY": [
                "simulate",
                "simulation",
                "fix",
                "refactor",
                "recommendation",
                "recommendations",
                "priority",
                "ranking",
                "priorities",
                "impact",
                "blast radius",
                "lineage",
                "linkage"
            ],

            "AST_QUERY": [
                "ast",
                "syntax",
                "tree",
                "node",
                "nodes",
                "visitor",
                "parse",
                "parsing"
            ],

            "METRIC_QUERY": [
                "metric",
                "metrics",
                "complexity",
                "loc",
                "lines of code",
                "maintainability",
                "size",
                "scale",
                "statistics"
            ],

            "DEPENDENCY_QUERY": [
                "dependency",
                "dependencies",
                "import",
                "imports",
                "import graph",
                "coupling",
                "dependents",
                "incoming",
                "outgoing"
            ],

            "CODE_QUERY": [
                "code",
                "source",
                "file",
                "implementation",
                "class",
                "method",
                "function",
                "lines",
                "extracted"
            ]
        }

        self.intent_sources = {
            "ARCHITECTURE_QUERY": [
                "repository_intelligence",
                "trust_vectors",
                "quantum_walk_results"
            ],

            "COMPONENT_QUERY": [
                "repository_intelligence",
                "trust_vectors"
            ],

            "RISK_QUERY": [
                "trust_vectors",
                "quantum_walk_results",
                "qaoa_results",
                "agent_verification"
            ],

            "COMPARISON_QUERY": [
                "trust_vectors",
                "qaoa_results",
                "agent_verification"
            ],

            "QUANTUM_QUERY": [
                "qsvm_results",
                "quantum_walk_results",
                "qaoa_results",
                "qvnn_results"
            ],

            "AGENT_QUERY": [
                "agent_verification"
            ],

            "TRACE_QUERY": [
                "repository_intelligence",
                "trust_vectors",
                "qsvm_results",
                "quantum_walk_results",
                "qaoa_results",
                "qvnn_results",
                "agent_verification"
            ],

            "METHODOLOGY_QUERY": [
                "repository_intelligence",
                "trust_vectors",
                "agent_verification"
            ],

            "DECISION_QUERY": [
                "repository_intelligence",
                "trust_vectors",
                "qaoa_results",
                "qvnn_results",
                "agent_verification"
            ],

            "AST_QUERY": [
                "repository_intelligence"
            ],

            "METRIC_QUERY": [
                "repository_intelligence",
                "trust_features",
                "trust_vectors",
                "agent_verification"
            ],

            "DEPENDENCY_QUERY": [
                "repository_intelligence",
                "trust_vectors",
                "quantum_walk_results"
            ],

            "CODE_QUERY": [
                "repository_intelligence",
                "trust_vectors"
            ]
        }

        self.priority = {
            "DECISION_QUERY": 2.8,
            "TRACE_QUERY": 2.5,
            "DEPENDENCY_QUERY": 2.4,
            "ARCHITECTURE_QUERY": 2.3,
            "COMPARISON_QUERY": 2.2,
            "QUANTUM_QUERY": 2.0,
            "RISK_QUERY": 1.9,
            "METHODOLOGY_QUERY": 1.8,
            "METRIC_QUERY": 1.7,
            "AGENT_QUERY": 1.6,
            "AST_QUERY": 1.5,
            "CODE_QUERY": 1.4,
            "COMPONENT_QUERY": 1.2
        }


    def route(
        self,
        query: str
    ) -> QueryIntent:
        """
        Determines best QUEST reasoning route.
        """

        # Clean query by removing path/component terms to prevent matching path tokens as query intents
        cleaned_words = []
        for word in query.lower().split():
            if ".py" in word or "/" in word or "\\" in word:
                continue
            cleaned_words.append(word)
        query_lower = " ".join(cleaned_words)


        scores = {}

        for intent, keywords in self.intent_keywords.items():

            matches = sum(
                1
                for keyword in keywords
                if keyword in query_lower
            )

            scores[intent] = (
                matches * self.priority[intent]
            )

        selected_intent = max(
            scores,
            key=scores.get
        )

        if scores[selected_intent] == 0:

            return QueryIntent(
                query=query,
                intent="UNKNOWN_QUERY",
                target_sources=[
                    "repository_intelligence",
                    "trust_vectors",
                    "agent_verification"
                ],
                confidence=0.2
            )

        confidence = min(
            scores[selected_intent] / 3,
            1.0
        )

        return QueryIntent(
            query=query,
            intent=selected_intent,
            target_sources=self.intent_sources[selected_intent],
            confidence=round(
                confidence,
                5
            )
        )


if __name__ == "__main__":

    router = QueryRouter()

    questions = [
        "Explain the architecture of this project",
        "What files are inside this repository?",
        "Why is repository_scanner.py risky?",
        "Compare repository_scanner.py and qsvm_classifier.py",
        "What did QAOA optimization decide?",
        "Trace repository_scanner.py from analysis to final decision",
        "How is QUEST different from traditional tools?"
    ]

    for question in questions:

        result = router.route(question)

        print(
            question,
            "->",
            result.intent,
            result.target_sources
        )