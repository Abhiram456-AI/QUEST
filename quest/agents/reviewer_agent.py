

"""
QUEST: Quantum Evaluation of Software Trust

Phase 4:
Autonomous Multi-Agent Verification Framework

Module:
Reviewer Agent

Purpose:
Analyzes software quality and reliability evidence generated from
Repository Intelligence and Trust Representation layers.

Responsibilities:
- detect maintainability concerns
- identify complexity risks
- review trust vector scores
"""


from typing import Dict, List

from quest.agents.base_agent import BaseAgent, AgentFinding


class ReviewerAgent(BaseAgent):
    """
    Autonomous reliability reviewer.

    Uses QUEST Trust Vectors to identify components requiring
    engineering attention.
    """

    def __init__(self):
        super().__init__(
            name="ReviewerAgent"
        )


    def analyze(
        self,
        context: Dict
    ) -> List[AgentFinding]:

        findings = []

        trust_vectors = context.get(
            "trust_vectors",
            []
        )


        for component in trust_vectors:

            file_path = component.get(
                "file_path",
                "unknown"
            )

            vector = component.get(
                "vector",
                [0, 0, 0, 0]
            )

            trust_score = component.get(
                "trust_score",
                0
            )


            complexity = vector[0]
            reliability = vector[3]


            if trust_score < 0.7:

                confidence = self.calculate_confidence(
                    [
                        1 - trust_score,
                        complexity,
                        1 - reliability
                    ]
                )

                findings.append(
                    self.create_finding(
                        component=file_path,
                        finding=(
                            "Component shows reduced reliability "
                            "based on trust analysis"
                        ),
                        severity="MEDIUM",
                        confidence=confidence,
                        evidence={
                            "trust_score": trust_score,
                            "complexity": complexity,
                            "reliability": reliability
                        }
                    )
                )


            if complexity > 0.5:

                findings.append(
                    self.create_finding(
                        component=file_path,
                        finding=(
                            "High structural complexity detected"
                        ),
                        severity="HIGH",
                        confidence=complexity,
                        evidence={
                            "complexity": complexity
                        }
                    )
                )


        return findings