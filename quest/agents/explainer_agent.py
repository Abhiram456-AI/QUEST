

"""
QUEST: Quantum Evaluation of Software Trust

Phase 4:
Autonomous Multi-Agent Verification Framework

Module:
Explainer Agent

Purpose:
Transforms multi-agent verification results into human-readable
reliability explanations.

Responsibilities:
- explain agent decisions
- summarize evidence chains
- connect quantum reasoning with developer understanding
"""


from typing import Dict, List

from quest.agents.base_agent import BaseAgent, AgentFinding


class ExplainerAgent(BaseAgent):
    """
    Autonomous explanation generation agent.

    Converts raw verification evidence into interpretable
    reliability explanations.
    """

    def __init__(self):
        super().__init__(
            name="ExplainerAgent"
        )


    def analyze(
        self,
        context: Dict
    ) -> List[AgentFinding]:

        explanations = []

        verifier_results = context.get(
            "verifier_findings",
            []
        )

        all_findings = context.get(
            "agent_findings",
            []
        )


        for decision in verifier_results:

            component = decision.get(
                "component",
                "repository"
            )

            if component == "repository":
                related_findings = all_findings
            else:
                related_findings = [
                    finding
                    for finding in all_findings
                    if finding.get("component") == component
                ]


            explanation = self.generate_explanation(
                decision,
                related_findings
            )


            explanations.append(
                self.create_finding(
                    component=component,
                    finding=explanation,
                    severity=decision.get(
                        "severity",
                        "INFO"
                    ),
                    confidence=decision.get(
                        "confidence",
                        0
                    ),
                    evidence={
                        "decision": decision.get(
                            "finding"
                        ),
                        "supporting_findings": len(
                            related_findings
                        )
                    }
                )
            )


        return explanations


    def generate_explanation(
        self,
        decision: Dict,
        findings: List[Dict]
    ) -> str:
        """
        Creates a developer-readable explanation.
        """

        decision_text = decision.get(
            "finding",
            "UNKNOWN_DECISION"
        )

        severity = decision.get(
            "severity",
            "UNKNOWN"
        )


        explanation = (
            f"QUEST verification result: {decision_text}. "
            f"Overall severity level is {severity}. "
        )


        if findings:

            explanation += (
                "The decision was generated after evaluating "
                f"{len(findings)} supporting agent findings. "
            )

            strongest = max(
                findings,
                key=lambda item: item.get(
                    "confidence",
                    0
                )
            )

            explanation += (
                "Strongest evidence: "
                f"{strongest.get('finding')}."
            )

        else:

            explanation += (
                "No additional reliability concerns were found "
                "during autonomous verification."
            )


        return explanation