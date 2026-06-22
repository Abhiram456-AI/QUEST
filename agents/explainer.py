from agents.base_agent import BaseAgent


class ExplainerAgent(BaseAgent):
    def __init__(self, query_engine):
        self.query_engine = query_engine

    """
    Converts technical findings into human-understandable
    explanations and recommendations.

    This is currently a stub implementation and will later be
    connected to an LLM.
    """

    def analyze(self, query, context=None):
        evidence = self.query_engine.query(query)

        if isinstance(evidence, dict) and "error" in evidence:
            return {
                "agent": "explainer",
                "query": query,
                "evidence": evidence,
                "summary": evidence["error"],
                "recommendation": (
                    "No risk assessment could be performed because the requested entity could not be resolved."
                ),
                "confidence": 0.72,
            }

        summaries = []
        recommendations = []
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

            node = item.get("node", "this module")
            level = item.get("risk_level", "UNKNOWN")
            score = float(item.get("risk_score", 0.0))
            metrics = item.get("metrics", {})
            reasons = item.get("reasons", [])

            explanation = (
                f"{node} is classified as {level} risk with a score of {score:.3f}."
            )

            fan_in = metrics.get("fan_in", 0)
            fan_out = metrics.get("fan_out", 0)
            centrality = metrics.get("centrality", 0)
            blast_radius = metrics.get("blast_radius", 0)

            details = []

            if fan_in > 0:
                details.append(
                    f"{fan_in} modules depend on it"
                )

            if fan_out > 0:
                details.append(
                    f"it depends on {fan_out} modules"
                )

            if blast_radius > 0:
                details.append(
                    f"changes may affect {blast_radius} files"
                )

            if centrality > 0.5:
                details.append(
                    "it occupies a highly central architectural position"
                )

            if details:
                explanation += " " + "; ".join(details) + "."

            if reasons:
                explanation += (
                    " Key indicators include: "
                    + ", ".join(reasons)
                    + "."
                )

            summaries.append(explanation)

            if level == "HIGH":
                recommendations.append(
                    f"Treat {node} as a critical module and introduce tests before modification."
                )

            elif level == "MEDIUM":
                recommendations.append(
                    f"Review dependencies and monitor changes to {node}."
                )

            elif level == "LOW":
                recommendations.append(
                    f"{node} currently presents relatively low repository risk."
                )

        summary = (
            " ".join(summaries)
            if summaries
            else "No explanation available."
        )

        recommendation = (
            " ".join(recommendations)
            if recommendations
            else "Further analysis is recommended."
        )

        if summaries:
            confidence = 0.90

        return {
            "agent": "explainer",
            "query": query,
            "evidence": evidence,
            "summary": summary,
            "recommendation": recommendation,
            "confidence": confidence,
        }
