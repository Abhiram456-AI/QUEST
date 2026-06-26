from typing import Optional
from agents.base_agent import BaseAgent


class ReviewerAgent(BaseAgent):
    """
    Performs the primary code review and identifies potential
    issues, risks, and areas that may require further analysis.

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
                "quantum_analysis": None,
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

            classical_score = score
            risk_score = max(risk_score, classical_score)

            findings.append(
                f"{node} is classified as {level} risk (score={score:.3f})."
            )

            for reason in reasons:
                findings.append(reason)

            fan_out = metrics.get("fan_out", 0)
            centrality = metrics.get("centrality", 0)
            blast_radius = metrics.get("blast_radius", 0)
            instability = metrics.get("instability", 0)

            qnode = self._get_quantum_node(node)

            if qnode is not None:
                risk_energy = getattr(qnode, "risk_energy", 0.0)
                qaoa_priority = getattr(qnode, "qaoa_priority", 0.0)
                qsvm_classification = getattr(
                    qnode,
                    "qsvm_classification",
                    "UNKNOWN",
                )
                qsvm_confidence = getattr(
                    qnode,
                    "qsvm_confidence",
                    0.5,
                )
                propagation_score = getattr(
                    qnode,
                    "propagation_score",
                    0.0,
                )
                stationary_probability = getattr(
                    qnode,
                    "stationary_probability",
                    0.0,
                )
                repo_influence = getattr(
                    qnode,
                    "repo_influence",
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
                quantum_confidence = getattr(
                    qnode,
                    "quantum_confidence",
                    0.5,
                )

                if risk_energy >= 0.80:
                    findings.append(
                        f"{node} exhibits very high quantum risk energy ({risk_energy:.3f})."
                    )

                if qaoa_priority >= 0.75:
                    findings.append(
                        f"QAOA strongly prioritizes {node} for review and verification."
                    )

                if (
                    qsvm_classification
                    == "HIGH_RISK"
                    and qsvm_confidence >= 0.80
                ):
                    findings.append(
                        f"QSVM classifies {node} as HIGH_RISK with confidence {qsvm_confidence:.2f}."
                    )

                if propagation_score >= 0.70:
                    findings.append(
                        f"Changes in {node} may propagate through repository dependencies."
                    )

                if stationary_probability >= 0.70:
                    findings.append(
                        f"{node} occupies a critical position in the dependency graph."
                    )

                if reliability_score <= 0.30:
                    findings.append(
                        f"{node} demonstrates low predicted reliability under repository changes."
                    )

                if uncertainty_score >= 0.50:
                    findings.append(
                        f"Quantum predictions for {node} exhibit elevated uncertainty and require additional verification."
                    )

                quantum_score = (
                    0.35 * risk_energy
                    + 0.25 * qaoa_priority
                    + 0.20 * propagation_score
                    + 0.20 * (1.0 - reliability_score)
                )

                quantum_score = self._clamp(
                    quantum_score
                )

                risk_score = max(
                    risk_score,
                    self._clamp(
                        0.50 * classical_score
                        + 0.50 * quantum_score
                    ),
                )

                agreement = (
                    1.0
                    - abs(
                        classical_score
                        - quantum_score
                    )
                )

                confidence = self._clamp(
                    (
                        0.30 * qsvm_confidence
                        + 0.30 * (1.0 - uncertainty_score)
                        + 0.20 * repo_influence
                        + 0.20 * agreement
                    ),
                    minimum=0.50,
                    maximum=0.95,
                )

                if propagation_score >= 0.70:
                    recommendations.append(
                        "Introduce regression tests before modifying this module."
                    )

                if qaoa_priority >= 0.75:
                    recommendations.append(
                        "Prioritize this module during code review and reliability verification."
                    )

                if reliability_score <= 0.30:
                    recommendations.append(
                        "Consider decomposing responsibilities and reducing dependency concentration."
                    )

                if uncertainty_score >= 0.50:
                    recommendations.append(
                        "Collect additional repository evidence before making structural modifications."
                    )

                if quantum_confidence >= 0.85:
                    findings.append(
                        f"Quantum analysis strongly supports the assessment of {node}."
                    )
                elif quantum_confidence <= 0.40:
                    findings.append(
                        f"Quantum analysis remains inconclusive for {node}."
                    )

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
            confidence = max(confidence, 0.72)

        findings = self._deduplicate(findings)
        recommendations = self._deduplicate(
            recommendations
        )

        quantum_analysis = None

        if modules:
            first = modules[0]
            if isinstance(first, dict):
                qnode = self._get_quantum_node(
                    first.get("node")
                )

                if qnode is not None:
                    quantum_analysis = {
                        "risk_energy": round(getattr(qnode, "risk_energy", 0.0), 3),
                        "qaoa_priority": round(getattr(qnode, "qaoa_priority", 0.0), 3),
                        "qsvm_classification": getattr(qnode, "qsvm_classification", "UNKNOWN"),
                        "qsvm_confidence": round(getattr(qnode, "qsvm_confidence", 0.5), 3),
                        "propagation_score": round(getattr(qnode, "propagation_score", 0.0), 3),
                        "stationary_probability": round(getattr(qnode, "stationary_probability", 0.0), 3),
                        "repo_influence": round(getattr(qnode, "repo_influence", 0.0), 3),
                        "reliability_score": round(getattr(qnode, "reliability_score", 1.0), 3),
                        "uncertainty_score": round(getattr(qnode, "uncertainty_score", 0.0), 3),
                        "quantum_confidence": round(getattr(qnode, "quantum_confidence", 0.5), 3),
                    }

        return {
            "agent": "reviewer",
            "query": query,
            "evidence": evidence,
            "findings": findings,
            "recommendations": recommendations,
            "risk_score": risk_score,
            "confidence": confidence,
            "quantum_analysis": quantum_analysis,
            "assessment_performed": (
                quantum_analysis is not None
            ),
        }