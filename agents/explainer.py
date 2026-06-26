from typing import Optional
from agents.base_agent import BaseAgent


class ExplainerAgent(BaseAgent):
    """
    Converts technical findings into human-understandable
    explanations and recommendations.

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
        seen = set()
        result = []

        for item in items:
            try:
                key = repr(item)
            except Exception:
                key = str(item)

            if key not in seen:
                seen.add(key)
                result.append(item)

        return result

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

        quantum_insights = []
        narrative_sections = []
        overall_quantum_confidence = 0.5
        explainability_score = 0.0
        repository_health_summary = ""

        narrative_coherence = 0.0
        explanation_labels = []
        explanation_coverage = 0.0
        repository_risk_distribution = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MODERATE": 0,
            "LOW": 0,
        }

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
            qnode = self._get_quantum_node(node)
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
                qsvm_classification = getattr(
                    qnode,
                    "qsvm_classification",
                    "UNKNOWN",
                )

                overall_quantum_confidence = max(
                    overall_quantum_confidence,
                    quantum_confidence,
                )

                explainability = self._clamp(
                    (
                        0.40 * quantum_confidence
                        + 0.30 * (1.0 - uncertainty_score)
                        + 0.30 * repo_influence
                    )
                )

                explainability_score = max(
                    explainability_score,
                    explainability,
                )

                if risk_energy >= 0.85:
                    risk_label = "CRITICAL"
                elif risk_energy >= 0.65:
                    risk_label = "HIGH"
                elif risk_energy >= 0.35:
                    risk_label = "MODERATE"
                else:
                    risk_label = "LOW"

                repository_risk_distribution[
                    risk_label
                ] += 1

                explanation_coverage += 1.0

                quantum_parts = []

                if risk_energy >= 0.80:
                    quantum_parts.append(
                        "quantum analysis predicts elevated repository risk"
                    )

                if propagation_score >= 0.70:
                    quantum_parts.append(
                        "changes may propagate widely through repository dependencies"
                    )

                if stationary_probability >= 0.70:
                    quantum_parts.append(
                        "the module occupies a structurally important position"
                    )

                if reliability_score <= 0.30:
                    quantum_parts.append(
                        "predicted reliability is relatively low"
                    )

                if uncertainty_score >= 0.50:
                    quantum_parts.append(
                        "quantum predictions contain elevated uncertainty"
                    )

                reliability_story = []

                if (
                    risk_energy >= 0.80
                    and propagation_score >= 0.70
                ):
                    reliability_story.append(
                        f"{node} represents a potential repository-wide failure hotspot"
                    )

                if (
                    repo_influence >= 0.75
                    and reliability_score <= 0.30
                ):
                    reliability_story.append(
                        f"{node} is highly influential but exhibits relatively poor predicted reliability"
                    )

                if uncertainty_score >= 0.50:
                    reliability_story.append(
                        f"predictions for {node} should be interpreted cautiously due to elevated uncertainty"
                    )

                if quantum_parts:
                    explanation += (
                        " Quantum perspective: "
                        + "; ".join(quantum_parts)
                        + "."
                    )

                    if reliability_story:
                        explanation += (
                            " Reliability interpretation: "
                            + ". ".join(reliability_story)
                            + "."
                        )

                narrative_sections.append(
                    f"For {node}, QSVM classified the module as {qsvm_classification}, quantum risk level was {risk_label}, QAOA assigned a review priority of {qaoa_priority:.3f}, and overall quantum confidence reached {quantum_confidence:.3f}."
                )

                if quantum_confidence >= 0.85:
                    confidence_label = "HIGH"
                elif quantum_confidence >= 0.65:
                    confidence_label = "MEDIUM"
                else:
                    confidence_label = "LOW"

                if explainability >= 0.80:
                    explainability_label = "HIGH"
                elif explainability >= 0.60:
                    explainability_label = "MEDIUM"
                else:
                    explainability_label = "LOW"

                explanation_labels.append(
                    explainability_label
                )

                quantum_insights.append(
                    {
                        "node": node,
                        "risk_energy": self._safe_round(risk_energy),
                        "qaoa_priority": self._safe_round(qaoa_priority),
                        "propagation_score": self._safe_round(propagation_score),
                        "stationary_probability": self._safe_round(stationary_probability),
                        "repo_influence": self._safe_round(repo_influence),
                        "reliability_score": self._safe_round(reliability_score),
                        "uncertainty_score": self._safe_round(uncertainty_score),
                        "quantum_confidence": self._safe_round(quantum_confidence),
                        "qsvm_classification": qsvm_classification,
                        "confidence_label": confidence_label,
                        "explainability_score": self._safe_round(
                            explainability
                        ),
                        "risk_label": risk_label,
                        "explainability_label": (
                            explainability_label
                        ),
                    }
                )

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

            if qnode is not None:
                if propagation_score >= 0.70:
                    recommendations.append(
                        f"Introduce regression tests before modifying {node}."
                    )

                if qaoa_priority >= 0.75:
                    recommendations.append(
                        f"Prioritize review and verification activities for {node}."
                    )

                if reliability_score <= 0.30:
                    recommendations.append(
                        f"Consider decomposing responsibilities and reducing dependency concentration in {node}."
                    )

                if uncertainty_score >= 0.50:
                    recommendations.append(
                        f"Collect additional repository evidence before major modifications to {node}."
                    )

        quantum_insights = self._deduplicate(
            quantum_insights
        )
        recommendations = self._deduplicate(
            recommendations
        )

        narrative = " ".join(narrative_sections)
        if modules:
            explanation_coverage /= float(
                len(modules)
            )

        narrative_coherence = self._clamp(
            (
                0.40 * overall_quantum_confidence
                + 0.30 * explainability_score
                + 0.30 * float(
                    len(quantum_insights) > 0
                )
            )
        )

        narrative_coherence = self._clamp(
            narrative_coherence
        )

        explanation_coverage = self._clamp(
            explanation_coverage
        )

        if overall_quantum_confidence >= 0.80:
            repository_health_summary = (
                "Quantum analysis produced highly confident repository assessments."
            )
        elif overall_quantum_confidence >= 0.60:
            repository_health_summary = (
                "Quantum analysis produced moderately confident repository assessments."
            )
        else:
            repository_health_summary = (
                "Quantum assessments remain exploratory and should be validated with additional evidence."
            )

        summary = (
            " ".join(summaries)
            if summaries
            else "No explanation available."
        )

        if narrative:
            summary += (
                " Quantum reasoning summary: "
                + narrative
            )

        summary += (
            " Repository health summary: "
            + repository_health_summary
        )
        summary += (
            " Repository risk distribution: "
            f"CRITICAL={repository_risk_distribution['CRITICAL']}, "
            f"HIGH={repository_risk_distribution['HIGH']}, "
            f"MODERATE={repository_risk_distribution['MODERATE']}, "
            f"LOW={repository_risk_distribution['LOW']}."
        )

        if explanation_labels:
            summary += (
                " Explainability level: "
                + max(
                    explanation_labels,
                    key=lambda label: {
                        "LOW": 0,
                        "MEDIUM": 1,
                        "HIGH": 2,
                    }.get(label, 0),
                )
                + "."
            )

        recommendations = self._deduplicate(
            recommendations
        )

        recommendation = (
            " ".join(recommendations)
            if recommendations
            else "Further analysis is recommended."
        )

        if summaries:
            confidence = max(
                0.72,
                self._clamp(
                    0.55
                    + 0.40
                    * overall_quantum_confidence,
                    minimum=0.50,
                    maximum=0.95,
                ),
            )

        confidence = self._clamp(
            confidence,
            minimum=0.50,
            maximum=0.95,
        )

        dominant_explainability = (
            max(
                explanation_labels,
                key=lambda label: {
                    "LOW": 0,
                    "MEDIUM": 1,
                    "HIGH": 2,
                }.get(label, 0),
            )
            if explanation_labels
            else "LOW"
        )

        return {
            "agent": "explainer",
            "query": query,
            "evidence": evidence,
            "summary": summary,
            "recommendation": recommendation,
            "confidence": confidence,
            "quantum_insights": quantum_insights,
            "quantum_confidence": self._safe_round(
                overall_quantum_confidence
            ),
            "assessment_performed": bool(
                quantum_insights
            ),
            "repository_health_summary": (
                repository_health_summary
            ),
            "explainability_score": self._safe_round(
                explainability_score
            ),
            "narrative_coherence": (
                self._safe_round(
                    narrative_coherence
                )
            ),
            "explanation_coverage": self._safe_round(
                explanation_coverage
            ),
            "repository_risk_distribution": (
                repository_risk_distribution
            ),
            "dominant_explainability": (
                dominant_explainability
            ),
        }
