"""
QUEST: Quantum Evaluation of Software Trust

Phase 4:
Autonomous Multi-Agent Verification Framework

Module:
Critic Agent

Purpose:
Validates and challenges findings produced by other QUEST agents.

Responsibilities:
- reduce false positives
- verify evidence strength
- challenge weak conclusions
- improve reliability of final decisions
"""

from typing import Dict, List

from quest.agents.base_agent import BaseAgent, AgentFinding


class CriticAgent(BaseAgent):
    """
    Autonomous adversarial review agent.

    Reviews outputs from other agents and determines whether
    findings are supported by sufficient evidence.
    """

    def __init__(self):
        super().__init__(
            name="CriticAgent"
        )

    def analyze(
        self,
        context: Dict
    ) -> List[AgentFinding]:

        findings = []

        agent_findings = context.get(
            "agent_findings",
            []
        )

        for finding in agent_findings:

            component = finding.get(
                "component",
                "unknown"
            )

            confidence = finding.get(
                "confidence",
                0
            )

            severity = finding.get(
                "severity",
                "LOW"
            )

            evidence = finding.get(
                "evidence",
                {}
            )

            evidence_strength = self.evaluate_evidence(
                evidence
            )

            if confidence < 0.4:

                findings.append(
                    self.create_finding(
                        component=component,
                        finding=(
                            "Finding requires additional verification "
                            "because confidence is limited"
                        ),
                        severity="LOW",
                        confidence=1 - confidence,
                        evidence={
                            "original_confidence": confidence,
                            "evidence_strength": evidence_strength
                        }
                    )
                )

            elif severity == "HIGH" and evidence_strength < 0.5:

                findings.append(
                    self.create_finding(
                        component=component,
                        finding=(
                            "High severity finding requires stronger "
                            "supporting evidence"
                        ),
                        severity="MEDIUM",
                        confidence=0.7,
                        evidence={
                            "original_severity": severity,
                            "evidence_strength": evidence_strength
                        }
                    )
                )

            else:

                findings.append(
                    self.create_finding(
                        component=component,
                        finding="Finding validated by critic reasoning",
                        severity="INFO",
                        confidence=self.calculate_confidence(
                            [
                                confidence,
                                evidence_strength
                            ]
                        ),
                        evidence={
                            "validation_status": "SUPPORTED"
                        }
                    )
                )

        return findings

    def evaluate_evidence(
        self,
        evidence: Dict
    ) -> float:
        """
        Calculates evidence completeness score.
        """

        if not evidence:
            return 0.0

        valid_items = sum(
            1
            for value in evidence.values()
            if value not in [None, {}, [], ""]
        )

        return round(
            valid_items / len(evidence),
            5
        )