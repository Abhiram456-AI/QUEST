import json
from typing import Dict, Any

class ExplanationValidator:
    """
    Validates synthesized conclusions and overrides contradictory risk and priority decisions.
    """

    def __init__(self):
        pass

    def validate(self, context: Dict[str, Any], initial_conclusion: str) -> Dict[str, Any]:
        """
        Validates the reasoning chain and overrides contradictory final decisions.
        """
        chain = context.get("reasoning_chain", {})
        component = context.get("component", "repository")
        
        # 1. Collect all agent severities with agent attribution
        agent_severities_map = {}
        agent_severities = []
        trust_score = 1.0
        for category_name, items in chain.items():
            for ev in items:
                content = ev.get("content", {})
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except Exception:
                        pass
                if isinstance(content, dict):
                    if "severity" in content:
                        agent = content.get("agent_name", category_name.split("_")[0].capitalize())
                        agent_severities_map[agent] = content["severity"]
                        agent_severities.append(content["severity"])
                    if "composite_trust_score" in content:
                        trust_score = content["composite_trust_score"]
                    elif "trust_score" in content:
                        trust_score = content["trust_score"]

        # 2. Check for Agent Disagreement (Consensus Score)
        disagreement_detected = False
        agreement_score = 1.0
        if agent_severities:
            from collections import Counter
            counts = Counter(agent_severities)
            most_common_count = counts.most_common(1)[0][1]
            agreement_score = most_common_count / len(agent_severities)
            
            # Map severities to values to compute range
            sev_vals = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
            active_vals = [sev_vals.get(s, 0) for s in agent_severities]
            val_range = max(active_vals) - min(active_vals) if active_vals else 0
            
            # Trigger severe disagreement if range is >= 3 steps (e.g. CRITICAL vs LOW) or consensus < 40%
            if len(agent_severities) >= 2 and (val_range >= 3 or agreement_score < 0.40):
                disagreement_detected = True

        # 3. Detect Contradictions
        has_high_concern = "HIGH" in agent_severities or "CRITICAL" in agent_severities or trust_score < 0.4
        
        validation_flagged = False
        validation_override = initial_conclusion
        
        if disagreement_detected:
            validation_flagged = True
            attributions = [f"{agent}: {sev}" for agent, sev in agent_severities_map.items()]
            validation_override = (
                f"Agent disagreement detected. "
                f"{', '.join(attributions)}. "
                f"Final Recommendation: REVIEW_REQUIRED. "
                f"Reason: Evidence sources disagree significantly."
            )
        elif has_high_concern and ("low risk" in initial_conclusion.lower() or "low remediation priority" in initial_conclusion.lower() or "low priority" in initial_conclusion.lower()):
            validation_flagged = True
            validation_override = (
                f"Overall, QUEST considers {component} to require REVIEW_REQUIRED priority based on contradictory risk signals. "
                f"Although some metrics suggest low baseline risk, active audits report HIGH/CRITICAL concerns or low trust. "
                f"Final Recommendation: REVIEW_REQUIRED."
            )

        return {
            "flagged": validation_flagged,
            "agreement_score": round(agreement_score, 4),
            "final_conclusion": validation_override
        }
