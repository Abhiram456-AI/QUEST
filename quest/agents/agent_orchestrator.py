

"""
QUEST: Quantum Evaluation of Software Trust

Phase 4:
Autonomous Multi-Agent Verification Framework

Module:
Agent Orchestrator

Purpose:
Coordinates all QUEST autonomous agents and manages the complete
multi-agent verification workflow.
"""


import json
from pathlib import Path
from dataclasses import asdict
from typing import Dict

from quest.agents.reviewer_agent import ReviewerAgent
from quest.agents.security_agent import SecurityAgent
from quest.agents.quantum_agent import QuantumAgent
from quest.agents.critic_agent import CriticAgent
from quest.agents.verifier_agent import VerifierAgent
from quest.agents.explainer_agent import ExplainerAgent


class AgentOrchestrator:
    """
    Executes the QUEST autonomous verification pipeline.

    Flow:
    Reviewer + Security + Quantum
                ↓
             Critic
                ↓
             Verifier
                ↓
             Explainer
    """

    def __init__(self):

        self.reviewer = ReviewerAgent()
        self.security = SecurityAgent()
        self.quantum = QuantumAgent()
        self.critic = CriticAgent()
        self.verifier = VerifierAgent()
        self.explainer = ExplainerAgent()


    def load_json(
        self,
        path: str
    ):

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)


    def execute(
        self
    ) -> Dict:

        context = {
            "repository_intelligence": self.load_json(
                "outputs/repository_intelligence.json"
            ),

            "trust_vectors": self.load_json(
                "outputs/trust_vectors.json"
            ),

            "qaoa_results": self.load_json(
                "outputs/quantum_results/qaoa_results.json"
            ),

            "qvnn_results": self.load_json(
                "outputs/quantum_results/qvnn_results.json"
            ),

            "quantum_walk_results": self.load_json(
                "outputs/quantum_results/quantum_walk_results.json"
            )
        }


        reviewer_results = self.reviewer.analyze(
            context
        )

        security_results = self.security.analyze(
            context
        )

        quantum_results = self.quantum.analyze(
            context
        )


        combined_findings = (
            reviewer_results
            + security_results
            + quantum_results
        )


        critic_context = {
            "agent_findings": [
                asdict(item)
                for item in combined_findings
            ]
        }

        critic_results = self.critic.analyze(
            critic_context
        )


        verifier_context = {
            "agent_findings": [
                asdict(item)
                for item in combined_findings
            ],

            "critic_findings": [
                asdict(item)
                for item in critic_results
            ]
        }

        verifier_results = self.verifier.analyze(
            verifier_context
        )


        explainer_context = {
            "agent_findings": [
                asdict(item)
                for item in combined_findings
            ],

            "verifier_findings": [
                asdict(item)
                for item in verifier_results
            ]
        }

        explanation_results = self.explainer.analyze(
            explainer_context
        )


        return {
            "reviewer": [asdict(item) for item in reviewer_results],
            "security": [asdict(item) for item in security_results],
            "quantum": [asdict(item) for item in quantum_results],
            "critic": [asdict(item) for item in critic_results],
            "verifier": [asdict(item) for item in verifier_results],
            "explanation": [asdict(item) for item in explanation_results]
        }


    def save_results(
        self,
        results: Dict,
        output_path="outputs/agent_results/verification_results.json"
    ):

        output = Path(output_path)

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
                results,
                file,
                indent=4
            )


if __name__ == "__main__":

    orchestrator = AgentOrchestrator()

    results = orchestrator.execute()

    orchestrator.save_results(
        results
    )

    print(
        "QUEST Autonomous Agent Verification Completed"
    )