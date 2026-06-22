

from agents.base_agent import BaseAgent


class ReviewerAgent(BaseAgent):
    def __init__(self, query_engine):
        self.query_engine = query_engine
    """
    Performs the primary code review and identifies potential
    issues, risks, and areas that may require further analysis.

    This is currently a stub implementation and will later be
    connected to an LLM.
    """

    def analyze(self, query, context=None):
        evidence = self.query_engine.query(query)
        if isinstance(evidence, dict) and "error" in evidence:
            return {
                "agent": "reviewer",
                "query": query,
                "evidence": evidence,
                "findings": [
                    evidence["error"],
                    "Risk assessment was not performed because the requested entity could not be resolved.",
                ],
                "recommendations": [],
                "risk_score": 0.0,
                "confidence": 0.72,
            }

        findings = []
        recommendations = []
        risk_score = 0.0
        confidence = 0.5

        modules = []

        if isinstance(evidence, list):
            modules = evidence
        elif isinstance(evidence, dict):
            if "highest_risk_modules" in evidence:
                modules = evidence["highest_risk_modules"]
            else:
                modules = [evidence]

        for item in modules:
            if not isinstance(item, dict):
                continue

            node = item.get("node", "unknown")
            level = item.get("risk_level", "UNKNOWN")
            score = float(item.get("risk_score", 0.0))
            metrics = item.get("metrics", {})
            reasons = item.get("reasons", [])

            risk_score = max(risk_score, score)

            findings.append(
                f"{node} is classified as {level} risk (score={score:.3f})."
            )

            for reason in reasons:
                findings.append(reason)

            fan_out = metrics.get("fan_out", 0)
            centrality = metrics.get("centrality", 0)
            blast_radius = metrics.get("blast_radius", 0)
            instability = metrics.get("instability", 0)

            if fan_out > 3:
                findings.append(
                    f"{node} has high fan-out ({fan_out}) and coordinates many components."
                )
                recommendations.append(
                    f"Consider decomposing {node} into smaller responsibilities."
                )

            if centrality > 0.5:
                findings.append(
                    f"{node} is highly central to repository architecture."
                )
                recommendations.append(
                    f"Protect {node} with stronger tests and code reviews."
                )

            if blast_radius > 3:
                findings.append(
                    f"Changes to {node} may impact {blast_radius} files."
                )

            if instability > 0.7:
                recommendations.append(
                    f"Introduce regression tests before modifying {node}."
                )

        if findings:
            confidence = 0.90

        return {
            "agent": "reviewer",
            "query": query,
            "evidence": evidence,
            "findings": findings,
            "recommendations": recommendations,
            "risk_score": risk_score,
            "confidence": confidence,
        }