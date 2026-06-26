from typing import Optional
from agents.base_agent import BaseAgent

class SecurityAgent(BaseAgent):
    """
    Evaluates repository structures and code relationships from a
    security and reliability perspective.

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

        issues = []
        impacted_files = []
        security_risk = 0.0
        confidence = 0.5

        propagation_hotspots = []
        critical_modules = []
        quantum_security_score = 0.0
        high_impact_modules = []

        review_priority_modules = []
        max_cascade_risk = 0.0

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
            qnode = self._get_quantum_node(node)
            score = float(item.get("risk_score", 0.0))
            metrics = item.get("metrics", {})

            classical_security = score
            security_risk = max(
                security_risk,
                classical_security,
            )

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

                quantum_component = self._clamp(
                    (
                        0.30 * risk_energy
                        + 0.25 * propagation_score
                        + 0.20 * repo_influence
                        + 0.15 * stationary_probability
                        + 0.10 * (1.0 - reliability_score)
                    )
                )

                quantum_security_score = max(
                    quantum_security_score,
                    quantum_component,
                )

                cascade_risk = self._clamp(
                    (
                        0.40 * propagation_score
                        + 0.35 * stationary_probability
                        + 0.25 * repo_influence
                    )
                )

                max_cascade_risk = max(
                    max_cascade_risk,
                    cascade_risk,
                )

                review_priority = self._clamp(
                    (
                        0.50 * qaoa_priority
                        + 0.30 * risk_energy
                        + 0.20 * propagation_score
                    )
                )

                agreement = self._clamp(
                    1.0
                    - abs(
                        classical_security
                        - quantum_component
                    )
                )

                if propagation_score >= 0.70:
                    issues.append(
                        f"{node} is a propagation hotspot and may distribute failures throughout the repository."
                    )
                    propagation_hotspots.append(node)

                if cascade_risk >= 0.75:
                    issues.append(
                        f"{node} presents a high probability of cascading repository failures."
                    )

                if stationary_probability >= 0.70:
                    issues.append(
                        f"{node} occupies a structurally critical position in the dependency graph."
                    )
                    critical_modules.append(node)

                if risk_energy >= 0.80:
                    issues.append(
                        f"Quantum risk analysis identifies {node} as a high-risk repository component."
                    )

                if qaoa_priority >= 0.75:
                    issues.append(
                        f"QAOA prioritizes {node} for immediate reliability and security verification."
                    )
                    review_priority_modules.append(node)

                if review_priority >= 0.80:
                    issues.append(
                        f"{node} should receive immediate review and verification attention."
                    )
                    review_priority_modules.append(node)

                if reliability_score <= 0.30:
                    issues.append(
                        f"{node} exhibits low predicted reliability under repository modifications."
                    )

                if (
                    reliability_score <= 0.30
                    and propagation_score >= 0.70
                ):
                    issues.append(
                        f"{node} combines low reliability with high propagation potential and should be treated as operationally critical."
                    )
                    high_impact_modules.append(node)

                if uncertainty_score >= 0.50:
                    issues.append(
                        f"Predictions for {node} contain elevated uncertainty and should be validated before major changes."
                    )

                if (
                    risk_energy >= 0.80
                    and propagation_score >= 0.70
                ):
                    issues.append(
                        f"{node} represents a repository-wide reliability hotspot."
                    )
                    high_impact_modules.append(node)

                if (
                    repo_influence >= 0.75
                    and reliability_score <= 0.30
                ):
                    issues.append(
                        f"{node} is highly influential and exhibits poor predicted reliability."
                    )
                    high_impact_modules.append(node)

                blended_security = self._clamp(
                    0.50 * classical_security
                    + 0.50 * quantum_component
                )

                security_risk = max(
                    security_risk,
                    blended_security,
                )

                confidence = max(
                    confidence,
                    self._clamp(
                        (
                            0.30 * quantum_confidence
                            + 0.20 * (1.0 - uncertainty_score)
                            + 0.20 * repo_influence
                            + 0.15 * stationary_probability
                            + 0.15 * agreement
                        ),
                        minimum=0.50,
                        maximum=0.95,
                    ),
                )

        review_priority_modules = self._deduplicate(
            review_priority_modules
        )
        issues = self._deduplicate(issues)
        propagation_hotspots = self._deduplicate(
            propagation_hotspots
        )
        critical_modules = self._deduplicate(
            critical_modules
        )
        high_impact_modules = self._deduplicate(
            high_impact_modules
        )
        impacted_files = sorted(set(impacted_files))

        if issues:
            confidence = max(confidence, 0.72)

        security_risk = self._clamp(
            security_risk
        )

        confidence = self._clamp(
            confidence,
            minimum=0.50,
            maximum=0.95,
        )

        quantum_analysis = {
            "propagation_hotspots": propagation_hotspots,
            "critical_modules": critical_modules,
            "high_impact_modules": high_impact_modules,
            "quantum_security_score": self._safe_round(
                quantum_security_score
            ),
            "cascade_risk": self._safe_round(
                max_cascade_risk
            ),
            "review_priority_modules": (
                review_priority_modules
            ),
            "risk_zone": (
                "CRITICAL"
                if quantum_security_score >= 0.85
                or max_cascade_risk >= 0.85
                else "HIGH"
                if quantum_security_score >= 0.65
                or max_cascade_risk >= 0.65
                else "MODERATE"
                if quantum_security_score >= 0.35
                or max_cascade_risk >= 0.35
                else "LOW"
            ),
        }

        return {
            "agent": "security",
            "query": query,
            "evidence": evidence,
            "issues": issues,
            "impacted_files": impacted_files,
            "security_risk": security_risk,
            "confidence": confidence,
            "propagation_hotspots": propagation_hotspots,
            "critical_modules": critical_modules,
            "high_impact_modules": high_impact_modules,
            "quantum_security_score": self._safe_round(
                quantum_security_score
            ),
            "quantum_analysis": quantum_analysis,
            "risk_zone": quantum_analysis[
                "risk_zone"
            ],
            "cascade_risk": self._safe_round(
                max_cascade_risk
            ),
            "review_priority_modules": (
                review_priority_modules
            ),
            "assessment_performed": bool(
                propagation_hotspots
                or critical_modules
                or high_impact_modules
                or review_priority_modules
                or quantum_security_score
                or max_cascade_risk
            ),
        }
