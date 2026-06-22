from agents.base_agent import BaseAgent

class VerifierAgent(BaseAgent):
    def __init__(self, query_engine):
        self.query_engine = query_engine

    """
    Aggregates evidence from all reasoning agents and produces
    the final reliability and verification decision.

    This is currently a stub implementation and will later be
    connected to an LLM and consensus logic.
    """

    def analyze(
        self,
        reviewer,
        critic,
        security,
        explainer,
        context=None,
    ):
        reviewer_error = (
            reviewer.get("evidence", {}).get("error")
            if isinstance(reviewer, dict)
            and isinstance(reviewer.get("evidence"), dict)
            else None
        )

        if reviewer_error:
            confidences = []
            for agent_result in [
                reviewer,
                critic,
                security,
                explainer,
            ]:
                if isinstance(agent_result, dict):
                    confidences.append(
                        float(agent_result.get("confidence", 0.0))
                    )

            participating_agents = len(confidences)
            support_signal = (
                sum(confidences) / participating_agents
                if participating_agents
                else 0.0
            )

            return {
                "agent": "verifier",
                "reviewer": reviewer,
                "critic": critic,
                "security": security,
                "explainer": explainer,
                "consensus_summary": {
                    "review_findings": len(
                        reviewer.get("findings", [])
                    ),
                    "critic_objections": (
                        len(critic.get("objections", []))
                        if isinstance(critic, dict)
                        else 0
                    ),
                    "security_issues": (
                        len(security.get("issues", []))
                        if isinstance(security, dict)
                        else 0
                    ),
                    "participating_agents": participating_agents,
                    "support_signal": round(
                        support_signal, 2
                    ),
                    "contradiction_penalty": 0.0,
                    "agreement_ratio": 1.0,
                },
                "reliability_score": round(
                    support_signal, 3
                ),
                "verification_status": "UNRESOLVED",
                "assessment_performed": False,
                "confidence": reviewer.get(
                    "confidence", support_signal
                ),
            }
        confidences = []

        for agent_result in [
            reviewer,
            critic,
            security,
            explainer,
        ]:
            if isinstance(agent_result, dict):
                confidence = float(
                    agent_result.get("confidence", 0.0)
                )
                confidences.append(confidence)

        findings_count = len(
            reviewer.get("findings", [])
        ) if isinstance(reviewer, dict) else 0

        issues_count = len(
            security.get("issues", [])
        ) if isinstance(security, dict) else 0

        objections_count = len(
            critic.get("objections", [])
        ) if isinstance(critic, dict) else 0

        support_signal = (
            sum(confidences) / len(confidences)
            if confidences
            else 0.0
        )

        contradictions = 0

        if isinstance(critic, dict):
            for objection in critic.get("objections", []):
                text = str(objection).lower()
                if any(
                    phrase in text
                    for phrase in [
                        "not high risk",
                        "not medium risk",
                        "not low risk",
                        "low risk",
                        "classification is incorrect",
                        "cannot determine risk",
                        "risk assessment is unreliable",
                        "metrics are insufficient",
                    ]
                ):
                    contradictions += 1

        contradiction_penalty = min(
            max(contradictions, objections_count) * 0.02,
            0.15,
        )

        agreement_ratio = round(
            max(0.0, 1.0 - contradiction_penalty),
            3,
        )

        reliability_score = round(
            min(
                1.0,
                (
                    support_signal * 0.7
                    + agreement_ratio * 0.3
                ),
            ),
            3,
        )

        reliability_score = max(
            0.0,
            min(1.0, reliability_score),
        )

        verification_status = (
            "VERIFIED"
            if reliability_score >= 0.90
            else "REVIEW_REQUIRED"
        )

        participating_agents = len(confidences)

        consensus_summary = {
            "review_findings": findings_count,
            "critic_objections": objections_count,
            "security_issues": issues_count,
            "participating_agents": participating_agents,
            "support_signal": round(support_signal, 2),
            "contradiction_penalty": round(contradiction_penalty, 2),
            "agreement_ratio": agreement_ratio,
        }

        return {
            "agent": "verifier",
            "reviewer": reviewer,
            "critic": critic,
            "security": security,
            "explainer": explainer,
            "consensus_summary": consensus_summary,
            "reliability_score": reliability_score,
            "verification_status": verification_status,
            "assessment_performed": True,
            "confidence": round(
                sum(confidences) / len(confidences),
                3,
            ) if confidences else reliability_score,
            "reviewer_confidence": (
                reviewer.get("confidence")
                if isinstance(reviewer, dict)
                else None
            ),
        }