from agents.base_agent import BaseAgent

class SecurityAgent(BaseAgent):
    def __init__(self, query_engine):
        self.query_engine = query_engine
    """
    Evaluates repository structures and code relationships from a
    security and reliability perspective.

    This is currently a stub implementation and will later be
    connected to an LLM.
    """

    def analyze(self, query, context=None):
        evidence = self.query_engine.query(query)

        issues = []
        impacted_files = []
        security_risk = 0.0
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
            score = float(item.get("risk_score", 0.0))
            metrics = item.get("metrics", {})

            security_risk = max(security_risk, score)

            blast_radius = item.get(
                "blast_radius",
                metrics.get("blast_radius", 0)
            )

            fan_in = item.get(
                "fan_in",
                metrics.get("fan_in", 0)
            )

            fan_out = item.get(
                "fan_out",
                metrics.get("fan_out", 0)
            )

            centrality = metrics.get("centrality", 0)

            module_impacted = item.get(
                "impacted_files",
                []
            )

            impacted_files.extend(module_impacted)

            if blast_radius >= 5:
                issues.append(
                    f"{node} has a large blast radius ({blast_radius} files may be affected)."
                )
            elif blast_radius > 0:
                issues.append(
                    f"Changes to {node} may propagate to {blast_radius} dependent files."
                )

            if fan_in >= 4:
                issues.append(
                    f"{node} is heavily depended upon and may become a single point of failure."
                )

            if fan_out >= 5:
                issues.append(
                    f"{node} has numerous dependencies and may introduce propagation risks."
                )

            if centrality > 0.5:
                issues.append(
                    f"{node} is architecturally central and requires careful review before modification."
                )

            if module_impacted:
                issues.append(
                    f"Impacted files for {node}: {', '.join(module_impacted)}"
                )

        impacted_files = sorted(set(impacted_files))

        if issues:
            confidence = 0.90

        return {
            "agent": "security",
            "query": query,
            "evidence": evidence,
            "issues": issues,
            "impacted_files": impacted_files,
            "security_risk": security_risk,
            "confidence": confidence,
        }
