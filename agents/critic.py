from agents.base_agent import BaseAgent


class CriticAgent(BaseAgent):
    def __init__(self, query_engine):
        self.query_engine = query_engine

    """
    Challenges assumptions made by other agents and looks for
    contradictions, missed edge cases, and weak reasoning.

    This is currently a stub implementation and will later be
    connected to an LLM.
    """

    def analyze(self, query, context=None):
        evidence = self.query_engine.query(query)

        objections = []
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

            fan_in = metrics.get("fan_in", 0)
            fan_out = metrics.get("fan_out", 0)
            centrality = metrics.get("centrality", 0)
            blast_radius = metrics.get("blast_radius", 0)
            instability = metrics.get("instability", 0)

            if level == "HIGH":
                objections.append(
                    f"{node} being HIGH risk does not automatically imply poor design."
                )

            if score >= 0.8:
                objections.append(
                    f"{node} may intentionally be highly connected because of its architectural responsibilities."
                )

            if fan_in >= 4:
                objections.append(
                    f"The high dependency concentration around {node} may be a deliberate shared-service design choice."
                )

            if fan_out >= 5:
                objections.append(
                    f"High fan-out in {node} may reflect orchestration responsibilities rather than excessive coupling."
                )

            if centrality > 0.5:
                objections.append(
                    f"Architectural centrality alone should not be interpreted as a defect in {node}."
                )

            if blast_radius > 3:
                objections.append(
                    f"A large blast radius for {node} indicates importance but does not necessarily indicate unreliability."
                )

            if instability > 0.7:
                objections.append(
                    f"High instability in {node} should be evaluated alongside test coverage and change history."
                )

            if reasons:
                objections.append(
                    f"Risk indicators for {node} should be interpreted in repository context and not in isolation."
                )

        if objections:
            confidence = 0.90

        return {
            "agent": "critic",
            "query": query,
            "evidence": evidence,
            "objections": objections,
            "confidence": confidence,
        }