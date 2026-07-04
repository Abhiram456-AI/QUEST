

"""
QUEST: Quantum Evaluation of Software Trust

Phase 4:
Autonomous Multi-Agent Verification Framework

Module:
Verifier Agent

Purpose:
Aggregates validated multi-agent evidence and generates the final
repository reliability verification decision.

Responsibilities:
- combine reviewer, security, quantum, and critic outputs
- perform consensus-based verification
- calculate final reliability confidence
"""


from typing import Dict, List

from quest.agents.base_agent import BaseAgent, AgentFinding


class VerifierAgent(BaseAgent):
    """
    Autonomous consensus verification agent.

    Produces the final reliability-aware decision from all
    QUEST agent findings.
    """

    def __init__(self):
        super().__init__(
            name="VerifierAgent"
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

        critic_findings = context.get(
            "critic_findings",
            []
        )


        if not agent_findings:

            return [
                self.create_finding(
                    component="repository",
                    finding=(
                        "No reliability concerns detected by QUEST agents"
                    ),
                    severity="INFO",
                    confidence=1.0,
                    evidence={
                        "status": "VERIFIED"
                    }
                )
            ]


        severity_scores = {
            "INFO": 0.1,
            "LOW": 0.25,
            "MEDIUM": 0.5,
            "HIGH": 0.85
        }


        accumulated_risk = 0
        confidence_values = []


        for finding in agent_findings:

            accumulated_risk += severity_scores.get(
                finding.get(
                    "severity",
                    "LOW"
                ),
                0.25
            )

            confidence_values.append(
                finding.get(
                    "confidence",
                    0
                )
            )


        average_risk = accumulated_risk / len(
            agent_findings
        )

        confidence = self.calculate_confidence(
            confidence_values
        )


        critic_support = len(
            [
                item
                for item in critic_findings
                if item.get(
                    "evidence",
                    {}
                ).get(
                    "validation_status"
                ) == "SUPPORTED"
            ]
        )


        if average_risk >= 0.7:
            decision = "HIGH_RELIABILITY_ATTENTION_REQUIRED"
            severity = "HIGH"

        elif average_risk >= 0.4:
            decision = "MODERATE_RELIABILITY_ATTENTION_REQUIRED"
            severity = "MEDIUM"

        else:
            decision = "REPOSITORY_RELIABILITY_ACCEPTABLE"
            severity = "LOW"


        findings.append(
            self.create_finding(
                component="repository",
                finding=decision,
                severity=severity,
                confidence=confidence,
                evidence={
                    "average_risk": round(
                        average_risk,
                        5
                    ),
                    "total_agent_findings": len(
                        agent_findings
                    ),
                    "critic_supported_findings": critic_support
                }
            )
        )


        return findings