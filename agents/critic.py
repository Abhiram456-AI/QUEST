from typing import Optional
from agents.base_agent import BaseAgent


class CriticAgent(BaseAgent):
    """
    Challenges assumptions made by other agents and looks for
    contradictions, missed edge cases, and weak reasoning.

    This is currently a stub implementation and will later be
    connected to an LLM.
    """

    def __init__(
        self,
        query_engine,
        quantum_context: Optional[object] = None,
    ):
        self.query_engine = query_engine
        self.quantum_context = quantum_context

    @staticmethod
    def _clamp(value, minimum=0.0, maximum=1.0):
        return max(minimum, min(maximum, float(value)))

    @staticmethod
    def _deduplicate(items):
        return list(dict.fromkeys(items))

    @staticmethod
    def _safe_round(value, digits=3):
        try:
            return round(float(value), digits)
        except (TypeError, ValueError):
            return round(0.0, digits)

    def _get_quantum_node(self, node):
        if self.quantum_context is None:
            return None

        getter = getattr(
            self.quantum_context,
            "get_node",
            None,
        )

        if callable(getter):
            return getter(node)

        return None

    def analyze(self, query, context=None):
        evidence = self.query_engine.query(query)

        objections = []
        confidence = 0.5

        skepticism_score = 0.0
        challenged_nodes = []

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
            challenged_nodes.append(node)
            level = item.get("risk_level", "UNKNOWN")
            score = float(item.get("risk_score", 0.0))
            metrics = item.get("metrics", {})
            reasons = item.get("reasons", [])

            fan_in = metrics.get("fan_in", 0)
            fan_out = metrics.get("fan_out", 0)
            centrality = metrics.get("centrality", 0)
            blast_radius = metrics.get("blast_radius", 0)
            instability = metrics.get("instability", 0)

            qnode = self._get_quantum_node(node)

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

            if qnode is not None:
                risk_energy = getattr(qnode, "risk_energy", 0.0)
                qaoa_priority = getattr(
                    qnode,
                    "qaoa_priority",
                    0.0,
                )
                propagation_score = getattr(
                    qnode,
                    "propagation_score",
                    0.0,
                )
                reliability_score = getattr(
                    qnode,
                    "reliability_score",
                    1.0,
                )
                uncertainty_score = getattr(
                    qnode,
                    "uncertainty_score",
                    0.0,
                )
                repo_influence = getattr(
                    qnode,
                    "repo_influence",
                    0.0,
                )
                qsvm_confidence = getattr(
                    qnode,
                    "qsvm_confidence",
                    0.5,
                )
                quantum_confidence = getattr(
                    qnode,
                    "quantum_confidence",
                    0.5,
                )

                if risk_energy >= 0.80:
                    objections.append(
                        f"High quantum risk energy for {node} should be interpreted alongside observed repository history and not treated as a deterministic failure indicator."
                    )

                if qaoa_priority >= 0.75:
                    objections.append(
                        f"QAOA prioritization of {node} may indicate architectural importance rather than an inherent design defect."
                    )

                if propagation_score >= 0.70:
                    objections.append(
                        f"High propagation potential in {node} indicates sensitivity to change but does not necessarily imply unreliability."
                    )

                if reliability_score <= 0.30:
                    objections.append(
                        f"Predicted low reliability for {node} should be validated against empirical evidence such as tests and change history."
                    )

                if uncertainty_score >= 0.50:
                    objections.append(
                        f"Quantum predictions for {node} exhibit elevated uncertainty and should not be considered conclusive."
                    )

                if quantum_confidence <= 0.40:
                    objections.append(
                        f"Quantum evidence for {node} remains inconclusive and warrants additional investigation."
                    )

                if (
                    risk_energy >= 0.80
                    and reliability_score >= 0.70
                ):
                    objections.append(
                        f"Quantum indicators for {node} disagree: high risk energy coexists with relatively high predicted reliability."
                    )

                if (
                    risk_energy <= 0.30
                    and propagation_score >= 0.70
                ):
                    objections.append(
                        f"Low local quantum risk for {node} may still produce significant repository-wide effects due to dependency propagation."
                    )

                agreement_penalty = abs(
                    risk_energy - reliability_score
                )

                quantum_skepticism = self._clamp(
                    (
                        0.25 * uncertainty_score
                        + 0.20 * (1.0 - qsvm_confidence)
                        + 0.20 * (1.0 - reliability_score)
                        + 0.15 * repo_influence
                        + 0.20 * agreement_penalty
                    )
                )

                skepticism_score = max(
                    skepticism_score,
                    quantum_skepticism,
                )

                confidence = max(
                    confidence,
                    self._clamp(
                        0.55
                        + 0.40 * quantum_skepticism,
                        minimum=0.50,
                        maximum=0.95,
                    ),
                )

        challenged_nodes = self._deduplicate(
            challenged_nodes
        )
        objections = self._deduplicate(objections)

        if objections:
            confidence = max(confidence, 0.72)

        quantum_analysis = None

        if modules:
            first = modules[0]
            if isinstance(first, dict):
                qnode = self._get_quantum_node(
                    first.get("node")
                )

                if qnode is not None:
                    quantum_analysis = {
                        "risk_energy": self._safe_round(
                            getattr(qnode, "risk_energy", 0.0)
                        ),
                        "qaoa_priority": self._safe_round(
                            getattr(qnode, "qaoa_priority", 0.0)
                        ),
                        "propagation_score": self._safe_round(
                            getattr(qnode, "propagation_score", 0.0)
                        ),
                        "repo_influence": self._safe_round(
                            getattr(qnode, "repo_influence", 0.0)
                        ),
                        "reliability_score": self._safe_round(
                            getattr(qnode, "reliability_score", 1.0)
                        ),
                        "uncertainty_score": self._safe_round(
                            getattr(qnode, "uncertainty_score", 0.0)
                        ),
                        "quantum_confidence": self._safe_round(
                            getattr(qnode, "quantum_confidence", 0.5)
                        ),
                        "skepticism_score": self._safe_round(
                            skepticism_score
                        ),
                    }

        confidence = self._clamp(
            confidence,
            minimum=0.50,
            maximum=0.95,
        )

        return {
            "agent": "critic",
            "query": query,
            "evidence": evidence,
            "objections": objections,
            "confidence": confidence,
            "quantum_analysis": quantum_analysis,
            "assessment_performed": (
                quantum_analysis is not None
            ),
            "challenged_nodes": challenged_nodes,
            "skepticism_score": self._safe_round(
                skepticism_score
            ),
        }