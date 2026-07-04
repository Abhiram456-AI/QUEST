

"""
QUEST: Quantum Evaluation of Software Trust

Phase 4:
Autonomous Multi-Agent Verification Framework

Module:
Quantum Agent

Purpose:
Interprets Quantum Trust Intelligence results generated in Phase 3.

Responsibilities:
- analyze QSVM trust classifications
- interpret Quantum Walk propagation risks
- evaluate QAOA optimization priorities
- reason over QVNN reliability predictions
"""


from typing import Dict, List

from quest.agents.base_agent import BaseAgent, AgentFinding


class QuantumAgent(BaseAgent):
    """
    Autonomous quantum reasoning agent.

    Converts quantum algorithm outputs into reliability findings.
    """

    def __init__(self):
        super().__init__(
            name="QuantumAgent"
        )


    def analyze(
        self,
        context: Dict
    ) -> List[AgentFinding]:

        findings = []

        qaoa_results = context.get(
            "qaoa_results",
            []
        )

        qvnn_results = context.get(
            "qvnn_results",
            []
        )

        quantum_walk = context.get(
            "quantum_walk_results",
            []
        )


        # QAOA repair priority reasoning
        for result in qaoa_results:

            rank = result.get(
                "quantum_priority_rank",
                999
            )

            component = result.get(
                "component",
                "unknown"
            )


            if rank <= 3:

                priority_score = result.get(
                    "priority_score",
                    0
                )

                findings.append(
                    self.create_finding(
                        component=component,
                        finding=(
                            "Quantum optimization identified this "
                            "component as a high repair priority"
                        ),
                        severity="HIGH",
                        confidence=priority_score,
                        evidence={
                            "qaoa_rank": rank,
                            "priority_score": priority_score
                        }
                    )
                )


        # Quantum Walk propagation reasoning
        for walk in quantum_walk:

            source = walk.get(
                "source_component",
                "unknown"
            )

            influential = walk.get(
                "most_influential_components",
                []
            )


            if influential:

                findings.append(
                    self.create_finding(
                        component=source,
                        finding=(
                            "Quantum Walk detected propagation influence "
                            "through the software graph"
                        ),
                        severity="MEDIUM",
                        confidence=0.75,
                        evidence={
                            "influential_components": influential
                        }
                    )
                )


        # QVNN reliability prediction reasoning
        for prediction in qvnn_results:

            reliability = prediction.get(
                "reliability_probability",
                1
            )

            if reliability < 0.5:

                findings.append(
                    self.create_finding(
                        component=str(
                            prediction.get(
                                "sample_id"
                            )
                        ),
                        finding=(
                            "QVNN predicts possible reliability degradation"
                        ),
                        severity="HIGH",
                        confidence=1 - reliability,
                        evidence={
                            "reliability_probability": reliability
                        }
                    )
                )


        return findings