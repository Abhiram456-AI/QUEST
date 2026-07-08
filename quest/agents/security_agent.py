

"""
QUEST: Quantum Evaluation of Software Trust

Phase 4:
Autonomous Multi-Agent Verification Framework

Module:
Security Agent

Purpose:
Analyzes security-oriented reliability risks using evidence generated
from Repository Intelligence and Trust Representation layers.

Responsibilities:
- evaluate security risk factors
- identify risky dependencies/components
- generate autonomous security findings
"""


from typing import Dict, List

from quest.agents.base_agent import BaseAgent, AgentFinding


class SecurityAgent(BaseAgent):
    """
    Autonomous security verification agent.

    Uses QUEST trust vectors and repository intelligence evidence
    to identify components that may introduce reliability risks.
    """

    def __init__(self):
        super().__init__(
            name="SecurityAgent"
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

        repository_data = context.get(
            "repository_intelligence",
            {}
        )


        dependency_lookup = {}

        for item in repository_data.get(
            "files",
            []
        ):

            dependency_lookup[
                item.get("file")
            ] = item.get(
                "dependencies",
                {}
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
            trust_score = component.get("trust_score", 0.0)

            security_risk = vector[2]
            dependency_factor = vector[1]

            if security_risk > 0.25:
                confidence = self.calculate_confidence(
                    [
                        security_risk,
                        dependency_factor,
                        1.0 - trust_score
                    ]
                )

                findings.append(
                    self.create_finding(
                        component=file_path,
                        finding=(
                            "Potential security-sensitive component "
                            "identified from risk indicators"
                        ),
                        severity="HIGH",
                        confidence=confidence,
                        evidence={
                            "security_risk": security_risk,
                            "dependency_factor": dependency_factor,
                            "dependencies": dependency_lookup.get(
                                file_path,
                                {}
                            )
                        }
                    )
                )

            elif security_risk > 0.1:
                confidence = self.calculate_confidence(
                    [
                        security_risk,
                        1.0 - trust_score
                    ]
                )

                findings.append(
                    self.create_finding(
                        component=file_path,
                        finding=(
                            "Moderate security attention recommended"
                        ),
                        severity="MEDIUM",
                        confidence=confidence,
                        evidence={
                            "security_risk": security_risk
                        }
                    )
                )


        return findings