import re
from typing import Optional
from agents.base_agent import BaseAgent

class VerifierAgent(BaseAgent):
    """
    Aggregates evidence from all reasoning agents and produces
    the final reliability and verification decision.

    This is currently a stub implementation and will later be
    connected to an LLM and consensus logic.
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
    def _safe_round(value, digits=3):
        try:
            return round(float(value), digits)
        except (TypeError, ValueError):
            return round(0.0, digits)

    @staticmethod
    def _safe_mean(values):
        values = [
            float(v)
            for v in values
            if isinstance(v, (int, float))
        ]
        return (
            sum(values) / len(values)
            if values
            else 0.0
        )

    @staticmethod
    def _safe_ratio(numerator, denominator):
        try:
            denominator = float(denominator)
            if denominator <= 0:
                return 0.0
            return float(numerator) / denominator
        except (TypeError, ValueError, ZeroDivisionError):
            return 0.0
    @staticmethod
    def _reliability_label(score):
        if score >= 0.85:
            return "VERY_HIGH"
        if score >= 0.70:
            return "HIGH"
        if score >= 0.50:
            return "MODERATE"
        return "LOW"

    def _safe_confidence(self, result):
        if not isinstance(result, dict):
            return 0.0

        try:
            confidence = float(result.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0

        return self._clamp(confidence)

    def _evidence_coverage(
        self,
        findings_count,
        issues_count,
        objections_count,
    ):
        findings_score = min(findings_count / 5.0, 1.0)
        security_score = min(issues_count / 3.0, 1.0)
        objections_score = min(objections_count / 3.0, 1.0)

        weighted_score = (
            findings_score * 0.40
            + security_score * 0.30
            + objections_score * 0.30
        )

        return self._clamp(weighted_score)

    def _contradiction_score(self, critic):
        if not isinstance(critic, dict):
            return 1.0, 0

        contradictions = 0

        contradiction_patterns = [
            r"not\s+high\s+risk",
            r"not\s+medium\s+risk",
            r"not\s+low\s+risk",
            r"classification.*incorrect",
            r"cannot\s+determine\s+risk",
            r"risk\s+assessment\s+is\s+unreliable",
            r"metrics\s+are\s+insufficient",
        ]

        for objection in critic.get("objections", []):
            text = str(objection).lower()
            if any(
                re.search(pattern, text)
                for pattern in contradiction_patterns
            ):
                contradictions += 1

        score = self._clamp(
            1.0 - (contradictions * 0.15)
        )
        return score, contradictions

    def _calibration_score(self, confidences):
        if not confidences:
            return 0.0

        average = sum(confidences) / len(confidences)
        spread = max(confidences) - min(confidences)
        calibration = average * (1.0 - min(spread, 1.0))
        return self._clamp(calibration)

    def _quantum_consensus(
        self,
        reviewer,
        critic,
        security,
        explainer,
    ):
        risk_signals = []
        confidence_signals = []
        explainability_signals = []
        skepticism_signals = []
        evidence_count = 0

        for agent in [
            reviewer,
            critic,
            security,
            explainer,
        ]:
            if not isinstance(agent, dict):
                continue

            qa = agent.get("quantum_analysis")

            if not isinstance(qa, dict):
                continue

            evidence_count += 1

            risk_signals.extend(
                [
                    qa.get("risk_energy"),
                    qa.get("cascade_risk"),
                    qa.get("quantum_security_score"),
                ]
            )

            confidence_signals.append(
                qa.get("quantum_confidence")
            )

            explainability_signals.append(
                qa.get("explainability_score")
            )

            skepticism_signals.append(
                qa.get("skepticism_score")
            )

        risk_score = self._safe_mean(
            risk_signals
        )
        confidence_score = self._safe_mean(
            confidence_signals
        )
        explainability_score = self._safe_mean(
            explainability_signals
        )
        skepticism_score = self._safe_mean(
            skepticism_signals
        )

        available = evidence_count > 0
        evidence_factor = self._clamp(
            self._safe_ratio(
                evidence_count,
                4.0,
            )
        )

        if not available:
            return {
                "score": 0.0,
                "confidence": 0.0,
                "available": False,
                "evidence_count": 0,
                "evidence_factor": 0.0,
            }

        score = self._clamp(
            (
                0.25 * risk_score
                + 0.20 * confidence_score
                + 0.20 * explainability_score
                + 0.20 * (1.0 - skepticism_score)
                + 0.15 * evidence_factor
            )
        )

        agreement = self._clamp(
            (
                confidence_score
                + explainability_score
                + (1.0 - skepticism_score)
            )
            / 3.0
        )

        return {
            "score": score,
            "confidence": agreement,
            "available": True,
            "evidence_count": evidence_count,
            "evidence_factor": self._safe_round(
                evidence_factor
            ),
        }

    def _determine_status(
        self,
        reliability_score,
        assessment_performed,
        quantum_agreement=0.0,
    ):
        if not assessment_performed:
            return "UNRESOLVED"

        if (
            reliability_score >= 0.85
            and quantum_agreement >= 0.80
        ):
            return "VERIFIED"

        if (
            reliability_score >= 0.70
            and quantum_agreement >= 0.60
        ):
            return "PARTIALLY_VERIFIED"

        if quantum_agreement < 0.40:
            return "REVIEW_REQUIRED"

        return "LOW_CONFIDENCE"

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
                confidences.append(
                    self._safe_confidence(agent_result)
                )

            participating_agents = len(confidences)
            support_signal = (
                self._safe_ratio(
                    sum(confidences),
                    participating_agents,
                )
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
                    "evidence_coverage": 0.0,
                    "calibration_score": 0.0,
                    "contradictions": 0,
                    "quantum_consensus": 0.0,
                    "quantum_agreement": 0.0,
                    "quantum_evidence_count": 0,
                    "quantum_assessment_performed": False,
                    "evidence_factor": 0.0,
                    "consensus_strength": 0.0,
                },
                "reliability_score": round(
                    support_signal, 3
                ),
                "evidence_coverage": 0.0,
                "calibration_score": 0.0,
                "agreement_ratio": 1.0,
                "contradictions": 0,
                "reliability_breakdown": {
                    "support_signal": round(
                        support_signal,
                        3,
                    ),
                    "evidence_coverage": 0.0,
                    "calibration_score": 0.0,
                    "agreement_ratio": 1.0,
                    "contradictions": 0,
                },
                "verification_status": "UNRESOLVED",
                "assessment_performed": False,
                "confidence": self._safe_round(
                    support_signal
                ),
                "consensus_strength": 0.0,
                "verification_explanation": (
                    "No assessment could be performed because the requested entity could not be resolved."
                ),
                "reliability_label": "LOW",
                "quantum_disagreement": 1.0,
                "quantum_participation_ratio": 0.0,
                "reliability_confidence": 0.0,
                "decision_matrix": {
                    "reliability": "LOW",
                    "verification": "UNRESOLVED",
                    "consensus": 0.0,
                    "agreement": 0.0,
                },
                "verifier_metadata": {
                    "version": "quantum_v1",
                    "agents_considered": 4,
                    "quantum_enabled": True,
                },
            }
        confidences = []
        verification_explanation = []
        reliability_label = "LOW"

        for agent_result in [
            reviewer,
            critic,
            security,
            explainer,
        ]:
            confidences.append(
                self._safe_confidence(agent_result)
            )

        findings_count = len(
            reviewer.get("findings", [])
        ) if isinstance(reviewer, dict) else 0

        issues_count = len(
            security.get("issues", [])
        ) if isinstance(security, dict) else 0

        objections_count = len(
            critic.get("objections", [])
        ) if isinstance(critic, dict) else 0

        support_signal = self._safe_ratio(
            sum(confidences),
            len(confidences),
        )

        contradiction_score, contradictions = (
            self._contradiction_score(critic)
        )

        contradiction_penalty = self._safe_round(
            1.0 - contradiction_score
        )

        agreement_ratio = self._safe_round(
            contradiction_score
        )

        evidence_coverage = self._safe_round(
            self._evidence_coverage(
                findings_count,
                issues_count,
                objections_count,
            )
        )

        calibration_score = self._safe_round(
            self._calibration_score(
                confidences
            )
        )

        quantum_consensus = (
            self._quantum_consensus(
                reviewer,
                critic,
                security,
                explainer,
            )
        )

        reliability_score = round(
            min(
                1.0,
                (
                    support_signal * 0.25
                    + evidence_coverage * 0.25
                    + calibration_score * 0.15
                    + agreement_ratio * 0.15
                    + quantum_consensus["score"] * 0.20
                ),
            ),
            3,
        )
        reliability_score = self._clamp(
            reliability_score
        )

        quantum_agreement = self._clamp(
            (
                agreement_ratio
                + quantum_consensus[
                    "confidence"
                ]
            )
            / 2.0
        )

        consensus_strength = self._clamp(
            (
                quantum_consensus["score"]
                + quantum_agreement
            )
            / 2.0
        )

        quantum_disagreement = self._clamp(
            1.0 - consensus_strength
        )
        reliability_confidence = self._clamp(
            (
                0.40
                * self._safe_mean(confidences)
                + 0.30
                * consensus_strength
                + 0.30
                * quantum_agreement
            )
        )

        verification_status = (
            self._determine_status(
                reliability_score,
                assessment_performed=True,
                quantum_agreement=quantum_agreement,
            )
        )

        reliability_label = (
            self._reliability_label(
                reliability_score
            )
        )

        if verification_status == "VERIFIED":
            verification_explanation.append(
                "Classical and quantum assessments strongly agree and support the final reliability verdict."
            )
        elif verification_status == "PARTIALLY_VERIFIED":
            verification_explanation.append(
                "Most evidence supports the assessment, although minor disagreements remain among the reasoning agents."
            )
        elif verification_status == "REVIEW_REQUIRED":
            verification_explanation.append(
                "Quantum and classical assessments disagree and require additional investigation."
            )
        else:
            verification_explanation.append(
                "Available evidence is insufficient for a highly reliable verification decision."
            )

        participating_agents = len(confidences)

        quantum_participation_ratio = (
            self._clamp(
                self._safe_ratio(
                    quantum_consensus[
                        "evidence_count"
                    ],
                    4.0,
                )
            )
        )

        consensus_summary = {
            "review_findings": findings_count,
            "critic_objections": objections_count,
            "security_issues": issues_count,
            "participating_agents": participating_agents,
            "support_signal": self._safe_round(support_signal, 2),
            "contradiction_penalty": self._safe_round(
                contradiction_penalty,
                2,
            ),
            "agreement_ratio": agreement_ratio,
            "evidence_coverage": evidence_coverage,
            "calibration_score": calibration_score,
            "contradictions": contradictions,
            "quantum_consensus": (
                self._safe_round(
                    quantum_consensus[
                        "score"
                    ]
                )
            ),
            "quantum_agreement": (
                self._safe_round(
                    quantum_agreement
                )
            ),
            "quantum_evidence_count": (
                quantum_consensus[
                    "evidence_count"
                ]
            ),
            "evidence_factor": (
                quantum_consensus[
                    "evidence_factor"
                ]
            ),
            "consensus_strength": (
                self._safe_round(
                    consensus_strength
                )
            ),
        }

        reliability_breakdown = {
            "support_signal": self._safe_round(
                support_signal
            ),
            "evidence_coverage": evidence_coverage,
            "calibration_score": calibration_score,
            "agreement_ratio": agreement_ratio,
            "contradictions": contradictions,
            "quantum_consensus": (
                self._safe_round(
                    quantum_consensus[
                        "score"
                    ]
                )
            ),
            "quantum_agreement": (
                self._safe_round(
                    quantum_agreement
                )
            ),
            "quantum_evidence_count": (
                quantum_consensus[
                    "evidence_count"
                ]
            ),
            "evidence_factor": (
                quantum_consensus[
                    "evidence_factor"
                ]
            ),
            "consensus_strength": (
                self._safe_round(
                    consensus_strength
                )
            ),
            "formula": {
                "support_weight": 0.25,
                "evidence_weight": 0.25,
                "calibration_weight": 0.15,
                "agreement_weight": 0.15,
                "quantum_weight": 0.20,
            },
        }

        decision_matrix = {
            "reliability": reliability_label,
            "verification": verification_status,
            "consensus": self._safe_round(
                consensus_strength
            ),
            "agreement": self._safe_round(
                quantum_agreement
            ),
        }

        reliability_score = self._safe_round(
            reliability_score
        )
        return {
            "agent": "verifier",
            "reviewer": reviewer,
            "critic": critic,
            "security": security,
            "explainer": explainer,
            "consensus_summary": consensus_summary,
            "reliability_score": reliability_score,
            "evidence_coverage": evidence_coverage,
            "calibration_score": calibration_score,
            "agreement_ratio": agreement_ratio,
            "contradictions": contradictions,
            "reliability_breakdown": reliability_breakdown,
            "verification_status": verification_status,
            "assessment_performed": True,
            "confidence": self._safe_round(
                reliability_confidence
            ),
            "reviewer_confidence": (
                reviewer.get("confidence")
                if isinstance(reviewer, dict)
                else None
            ),
            "quantum_consensus": (
                self._safe_round(
                    quantum_consensus[
                        "score"
                    ]
                )
            ),
            "quantum_agreement": (
                self._safe_round(
                    quantum_agreement
                )
            ),
            "quantum_assessment_performed": (
                quantum_consensus[
                    "available"
                ]
            ),
            "quantum_evidence_count": (
                quantum_consensus[
                    "evidence_count"
                ]
            ),
            "consensus_strength": (
                self._safe_round(
                    consensus_strength
                )
            ),
            "verification_explanation": " ".join(
                verification_explanation
            ),
            "reliability_label": reliability_label,
            "decision_matrix": decision_matrix,
            "verifier_version": "quantum_v1",
            "verifier_metadata": {
                "version": "quantum_v1",
                "agents_considered": 4,
                "quantum_enabled": True,
            },
            "quantum_disagreement": (
                self._safe_round(
                    quantum_disagreement
                )
            ),
            "quantum_participation_ratio": (
                self._safe_round(
                    quantum_participation_ratio
                )
            ),
            "reliability_confidence": (
                self._safe_round(
                    reliability_confidence
                )
            ),
        }