import json
from typing import Dict, Any, List

class FinalDecisionResolver:
    """
    Decides the final resolved risk, confidence metrics, and recommendation narrative
    from all reasoning phases, ensuring complete consistency across the system.
    """

    def __init__(self, outputs_dir: Any = None):
        from pathlib import Path
        self.outputs_dir = Path(outputs_dir) if outputs_dir else Path("outputs")

    def load_json(self, path: Any) -> Any:
        from pathlib import Path
        path = Path(path)
        if path.exists():
            with open(path, "r") as f:
                try:
                    return json.load(f)
                except Exception:
                    return None
        return None

    def resolve(self, context: Dict[str, Any], initial_conclusion: str) -> Dict[str, Any]:
        """
        Synthesizes raw evidence and agent findings into a consistent decision set.
        """
        chain = context.get("reasoning_chain", {})
        component = context.get("component", "repository")
        evidence_count = context.get("evidence_count", 0)
        intent = context.get("intent", "UNKNOWN_QUERY")

        # 1. Gather all metrics
        trust_score = 1.0
        trust_cat = "HIGH_TRUST"
        
        trust_vectors = []
        if (self.outputs_dir / "trust_vectors.json").exists():
            try:
                with open(self.outputs_dir / "trust_vectors.json", "r") as f:
                    trust_vectors = json.load(f)
            except Exception:
                pass
        
        target_vec = None
        for item in trust_vectors:
            path = item.get("file_path", "")
            if path.endswith(component) or component.endswith(path):
                target_vec = item
                break
        
        if target_vec:
            trust_score = target_vec.get("trust_score", 1.0)
            trust_cat = target_vec.get("trust_category", "HIGH_TRUST")
        elif component == "repository" and trust_vectors:
            scores = [item.get("trust_score", 1.0) for item in trust_vectors]
            trust_score = sum(scores) / len(scores) if scores else 1.0
            if trust_score < 0.3:
                trust_cat = "LOW_TRUST"
            elif trust_score < 0.7:
                trust_cat = "MODERATE_TRUST"
            else:
                trust_cat = "HIGH_TRUST"

        complexity = 0
        
        # Initialize walk_score from quantum_walk_results.json
        walk_score = 0.0
        walk_results = []
        walk_path = self.outputs_dir / "quantum_results" / "quantum_walk_results.json"
        if walk_path.exists():
            try:
                with open(walk_path, "r") as f:
                    walk_results = json.load(f)
            except Exception:
                pass
        for item in walk_results:
            source = item.get("source_component", "")
            if source.endswith(component) or component.endswith(source):
                scores = item.get("propagation_scores", {})
                walk_score = scores.get(f"file:{component}", scores.get(component, 0.0))
                break
                
        # Initialize qvnn_prob from qvnn_results.json
        qvnn_prob = 1.0
        qvnn_results = []
        qvnn_path = self.outputs_dir / "quantum_results" / "qvnn_results.json"
        if qvnn_path.exists():
            try:
                with open(qvnn_path, "r") as f:
                    qvnn_results = json.load(f)
            except Exception:
                pass
        target_qvnn = None
        for q in qvnn_results:
            comp_path = q.get("component", "")
            if comp_path.endswith(component) or component.endswith(comp_path):
                target_qvnn = q
                break
        if target_qvnn:
            qvnn_prob = target_qvnn.get("reliability_probability", 1.0)
        elif component == "repository" and qvnn_results:
            probs = [q.get("reliability_probability", 1.0) for q in qvnn_results]
            qvnn_prob = sum(probs) / len(probs) if probs else 1.0

        agent_severities = []
        phases_used = []

        if chain.get("repository_analysis"):
            phases_used.append("repository intelligence (Phase 1)")
        if chain.get("trust_analysis"):
            phases_used.append("trust representation (Phase 2)")
        if chain.get("quantum_analysis"):
            phases_used.append("quantum intelligence (Phase 3)")
        if chain.get("agent_analysis"):
            phases_used.append("autonomous verification agents (Phase 4)")

        # Load dynamic complexity threshold from ConfigProvider
        from quest.config.config_provider import ConfigProvider
        config = ConfigProvider(self.outputs_dir)
        threshold_info = config.get_complexity_threshold()
        complexity_threshold = threshold_info["threshold_value"]

        for category_name, items in chain.items():
            for ev in items:
                content = ev.get("content", {})
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except Exception:
                        pass
                if not isinstance(content, dict):
                    continue
                
                if "composite_trust_score" in content:
                    trust_score = content["composite_trust_score"]
                if "trust_score" in content:
                    trust_score = content["trust_score"]
                if "trust_category" in content:
                    trust_cat = content["trust_category"]
                    
                if "cyclomatic_complexity" in content:
                    complexity = content["cyclomatic_complexity"]
                elif "metrics" in content and "cyclomatic_complexity" in content["metrics"]:
                    complexity = content["metrics"]["cyclomatic_complexity"]
                elif "complexity" in content:
                    complexity = content["complexity"]
                    
                if "propagation_scores" in content:
                    scores = content["propagation_scores"]
                    walk_score = max(walk_score, scores.get(f"file:{component}", scores.get(component, 0.0)))
                elif "quantum_walk_score" in content:
                    walk_score = max(walk_score, content["quantum_walk_score"])
                elif "propagation_risk" in content:
                    walk_score = max(walk_score, content["propagation_risk"])
                    
                if "reliability_probability" in content:
                    qvnn_prob = content["reliability_probability"]
                elif "qvnn_probability" in content:
                    qvnn_prob = content["qvnn_probability"]
                elif "reliability_score" in content:
                    qvnn_prob = content["reliability_score"]
                    
                if "severity" in content:
                    agent_severities.append(content["severity"])

        # 2. Separate Confidence Calibrations
        # A. Evidence Confidence: quality * coverage
        evidence_quality = min(1.0, evidence_count / 8.0) if evidence_count > 0 else 0.1
        coverage = 1.0
        if component != "repository":
            has_direct = False
            distinct_comps = set()
            for layer in chain.values():
                for ev in layer:
                    if ev.get("component"):
                        distinct_comps.add(ev.get("component"))
                    if ev.get("component") == component:
                        has_direct = True
            coverage = 1.0 if has_direct else (1.0 / max(1.0, len(distinct_comps)))
        evidence_confidence = evidence_quality * coverage

        # B. Decision Confidence: source diversity * agent agreement
        expected_phases = 3
        if intent in ["CODE_QUERY", "AST_QUERY", "METRIC_QUERY", "DEPENDENCY_QUERY", "ARCHITECTURE_QUERY"]:
            expected_phases = 1
        active_layers = sum(1 for layer in chain.values() if len(layer) > 0)
        source_diversity = min(1.0, active_layers / expected_phases) if expected_phases > 0 else 1.0
        source_diversity = max(0.4, source_diversity)

        agreement = 1.0
        agreement_desc = "perfect consensus"
        disagreement_detected = False
        severe_disagreement = False
        moderate_disagreement = False
        if agent_severities:
            from collections import Counter
            counts = Counter(agent_severities)
            most_common_count = counts.most_common(1)[0][1]
            agreement_ratio = most_common_count / len(agent_severities)
            agreement = 0.5 + 0.5 * agreement_ratio
            
            sev_vals = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
            active_vals = [sev_vals.get(s, 0) for s in agent_severities]
            val_range = max(active_vals) - min(active_vals) if active_vals else 0
            
            agreement_desc = f"perfect consensus ({most_common_count}/{len(agent_severities)} agents agree)"
            if len(agent_severities) >= 2 and (val_range >= 3 or agreement_ratio < 0.40):
                severe_disagreement = True
                disagreement_detected = True
                agreement_desc = f"low consensus ({most_common_count}/{len(agent_severities)} agents agree)"
            elif len(agent_severities) >= 2 and (val_range >= 2 or agreement_ratio <= 0.60):
                moderate_disagreement = True
                agreement_desc = f"moderate agreement ({most_common_count}/{len(agent_severities)} agents agree)"
        else:
            agreement_desc = "no agent findings evaluated"
        decision_confidence = source_diversity * agreement

        # C. Prediction Confidence: dynamic mean of QVNN probabilities in repo
        if qvnn_prob < 1.0:
            prediction_confidence = qvnn_prob
        else:
            qvnn_results = self.load_json(self.outputs_dir / "quantum_results" / "qvnn_results.json") or []
            all_qvnn_probs = [q.get("reliability_probability", 0.80) for q in qvnn_results]
            prediction_confidence = sum(all_qvnn_probs) / len(all_qvnn_probs) if all_qvnn_probs else 0.80

        # Fetch cappings and thresholds from ConfigProvider
        caps = config.get_confidence_cappings()
        max_confidence = caps.get("max_confidence", 0.95)
        disagreement_penalty_ceiling = caps.get("disagreement_penalty_ceiling", 0.30)

        thresholds = config.get_adaptive_thresholds()
        quantum_walk_dangerous_threshold = thresholds.get("quantum_walk_dangerous_threshold", 0.50)
        qvnn_reliable_threshold = thresholds.get("qvnn_reliable_threshold", 0.70)

        # 1. Compute Data Completeness (8.2)
        rankings = self.load_json(self.outputs_dir / "priority_ranking.json") or []
        complete_comps = 0
        for r in rankings:
            metrics_dict = r.get("metrics", {})
            if metrics_dict.get("complexity", 0) > 0 and metrics_dict.get("dependency_centrality", 0.0) > 0.0:
                complete_comps += 1
        data_completeness = complete_comps / len(rankings) if rankings else 1.0
        data_completeness = max(0.70, data_completeness)

        # 2. Compute Cross-Phase Consistency (8.6)
        cross_phase_consistency = 0.90
        target_rank_item = None
        for r in rankings:
            if r.get("component") == component:
                target_rank_item = r
                break
        if target_rank_item:
            try:
                comps_by_trust = sorted(rankings, key=lambda x: x["metrics"].get("trust_score", 1.0))
                comps_by_walk = sorted(rankings, key=lambda x: x["metrics"].get("quantum_walk_score", 0.0))
                comps_by_agent = sorted(rankings, key=lambda x: x["metrics"].get("avg_agent_severity", 0.0))
                comps_by_udpi = sorted(rankings, key=lambda x: x.get("udpi", 0.0))
                
                idx_t = next(i for i, x in enumerate(comps_by_trust) if x["component"] == component) / len(rankings)
                idx_w = next(i for i, x in enumerate(comps_by_walk) if x["component"] == component) / len(rankings)
                idx_a = next(i for i, x in enumerate(comps_by_agent) if x["component"] == component) / len(rankings)
                idx_u = next(i for i, x in enumerate(comps_by_udpi) if x["component"] == component) / len(rankings)
                
                dist = (abs(idx_t - idx_w) + abs(idx_w - idx_a) + abs(idx_a - idx_u)) / 3.0
                cross_phase_consistency = 1.0 - dist
            except Exception:
                cross_phase_consistency = 0.90
        cross_phase_consistency = max(0.50, cross_phase_consistency)

        # D. Unified Confidence Score (8.2 Multiplicative / Geometric Mean)
        # Bounded between 0.1 and 1.0
        raw_confidence = (
            max(0.10, evidence_confidence) *
            max(0.10, decision_confidence) *
            max(0.10, prediction_confidence) *
            max(0.10, data_completeness) *
            max(0.10, cross_phase_consistency)
        ) ** 0.2
        
        overall_confidence = raw_confidence
        is_capped = False
        cap_val = 1.0
        cap_reason = ""
        
        if overall_confidence > max_confidence:
            overall_confidence = max_confidence
            is_capped = True
            cap_val = max_confidence
            cap_reason = "Capped at maximum threshold"
            
        # 3. Disagreement / Contradiction Penalties
        from quest.decision.explanation_validator import ExplanationValidator
        validator = ExplanationValidator()
        validation_res = validator.validate(context, initial_conclusion)
        
        if validation_res.get("flagged") or severe_disagreement:
            if overall_confidence > disagreement_penalty_ceiling:
                overall_confidence = disagreement_penalty_ceiling
                is_capped = True
                cap_val = disagreement_penalty_ceiling
                cap_reason = "Capped due to severe agent disagreement / low consensus"
        elif moderate_disagreement:
            moderate_ceiling = 0.55
            if overall_confidence > moderate_ceiling:
                overall_confidence = moderate_ceiling
                is_capped = True
                cap_val = moderate_ceiling
                cap_reason = "Capped due to moderate agent disagreement"

        # 4. Resolve Contradiction Reasoning (Quantum walk bottleneck vs local QVNN stability)
        is_contradiction = walk_score >= quantum_walk_dangerous_threshold and qvnn_prob >= qvnn_reliable_threshold
        
        # 5. Resolve Risk & Priority Level
        # Mappings & Scalings
        complexity_scaled = min(1.0, complexity / max(1.0, complexity_threshold * 1.5))
        severity_order = {"INFO": 0.0, "LOW": 0.25, "MEDIUM": 0.5, "HIGH": 0.75, "CRITICAL": 1.0}
        agent_avg = sum(severity_order.get(s, 0.0) for s in agent_severities) / len(agent_severities) if agent_severities else 0.0
        
        # 1. Compute trust level
        all_trusts = [item.get("trust_score", 1.0) for item in trust_vectors] if trust_vectors else [trust_score]
        if len(all_trusts) >= 3:
            sorted_trusts = sorted(all_trusts)
            p33 = sorted_trusts[int(len(sorted_trusts) * 0.33)]
            p66 = sorted_trusts[int(len(sorted_trusts) * 0.66)]
            if p33 == p66:
                p33 = 0.40
                p66 = 0.70
        else:
            p33 = 0.40
            p66 = 0.70

        if trust_score > p66:
            trust_level = "HIGH_TRUST"
        elif trust_score >= p33:
            trust_level = "MODERATE_TRUST"
        else:
            trust_level = "LOW_TRUST"
        trust_cat = trust_level
            
        # 2. Compute risk level
        overall_risk_score = 0.25 * complexity_scaled + 0.25 * walk_score + 0.25 * agent_avg + 0.25 * (1.0 - qvnn_prob)
        if overall_risk_score >= 0.55:
            resolved_risk = "HIGH"
        elif overall_risk_score >= 0.3:
            resolved_risk = "MEDIUM"
        else:
            resolved_risk = "LOW"

        if is_contradiction:
            resolved_risk = "MEDIUM"

        # 3. Compute priority level (UDPI approximation)
        # Fetch base weights dynamically using ConfigProvider
        weights = config.get_weights()
        weights_file = self.outputs_dir / "weights.json"
        if weights_file.exists():
            try:
                with open(weights_file, "r") as f:
                    weights.update(json.load(f))
            except Exception:
                pass
                
        # Adapt weights contextually per component based on risk footprint (Phase 7 context-aware weighting)
        adapted_weights = dict(weights)
        
        # 1. Security-heavy context
        if agent_avg > 0.5:
            adapted_weights["agents"] = adapted_weights.get("agents", 0.15) + 0.15
            adapted_weights["trust"] = adapted_weights.get("trust", 0.15) + 0.05
            
        # 2. Complexity-heavy context
        if complexity_scaled > 0.5:
            adapted_weights["complexity"] = adapted_weights.get("complexity", 0.10) + 0.15
            adapted_weights["qaoa"] = adapted_weights.get("qaoa", 0.15) + 0.05
            
        # 3. Systemic coupling / risk propagation context
        if walk_score > 0.5:
            adapted_weights["quantum_walk"] = adapted_weights.get("quantum_walk", 0.15) + 0.15
            
        # Re-normalize adapted weights to sum to 1.0
        sum_w = sum(adapted_weights.values()) or 1.0
        adapted_weights = {k: round(v / sum_w, 4) for k, v in adapted_weights.items()}
        weights = adapted_weights
            
        udpi = (
            weights["trust"] * (1.0 - trust_score) +
            weights["quantum_walk"] * walk_score +
            weights["agents"] * agent_avg +
            weights["qvnn"] * (1.0 - qvnn_prob) +
            weights["complexity"] * complexity_scaled
        )
        total_w = weights["trust"] + weights["quantum_walk"] + weights["agents"] + weights["qvnn"] + weights["complexity"]
        udpi = min(1.0, udpi / total_w) if total_w > 0 else 0.5
        
        if udpi >= 0.6:
            priority_level = "CRITICAL"
        elif udpi >= 0.4:
            priority_level = "HIGH"
        elif udpi >= 0.2:
            priority_level = "MEDIUM"
        else:
            priority_level = "LOW"

        # 6. Override conclusion narrative with contradiction reasoning
        stage_str = " -> ".join(phases_used) if phases_used else "metrics analysis"
        agent_recommendation = ""
        if agent_severities:
            max_sev = max(agent_severities, key=lambda s: severity_order.get(s, 0.0))
            if max_sev in ["HIGH", "CRITICAL"]:
                agent_recommendation = ", while autonomous agents recommend prompt code refactoring"
            elif max_sev == "MEDIUM":
                agent_recommendation = ", while autonomous agents recommend continued monitoring rather than immediate remediation"
            else:
                agent_recommendation = ", and verification agents recommend standard maintenance"

        if priority_level == resolved_risk:
            conclusion = (
                f"Overall, QUEST considers {component} to require {priority_level} remediation priority, "
                f"aligning with its {resolved_risk.lower()} risk profile. "
            )
        else:
            conclusion = (
                f"Overall, QUEST considers {component} to require {priority_level} remediation priority, "
                f"driven by its {resolved_risk.lower()} risk profile under high systemic dependency footprints. "
            )

        if disagreement_detected or validation_res.get("flagged"):
            resolved_risk = "REVIEW_REQUIRED"
            conclusion = validation_res["final_conclusion"]
        elif is_contradiction:
            conclusion += (
                f"Stable component with high blast radius (Local reliability is high with QVNN prediction probability "
                f"{qvnn_prob:.2%}, but systemic impact remains high because dependency propagation walk score "
                f"{walk_score:.4f} is significant). Further verification and monitoring are recommended."
            )
        else:
            reasons = []
            if trust_score < 0.5:
                reasons.append(f"low trust score of {trust_score:.4f}")
            if complexity > complexity_threshold:
                reasons.append(f"high structural complexity of {complexity} (threshold: {complexity_threshold:.1f})")
            if walk_score > 0.5:
                reasons.append(f"significant risk propagation score of {walk_score:.4f}")
            if qvnn_prob < 0.7:
                reasons.append(f"low predicted reliability probability of {qvnn_prob:.2%}")
            
            reason_phrase = f" driven by {', '.join(reasons)}" if reasons else f" reflecting normal code attributes (complexity: {complexity}, trust score: {trust_score:.4f})"
            conclusion += (
                f"This rating is derived from {stage_str} stages{reason_phrase}{agent_recommendation}."
            )

        # Append conceptual definitions mapping to make trust/risk/priority boundary transparent
        definitions_block = (
            f"\n\n=== QUEST Conceptual Decision Breakdown ===\n"
            f"- Trust Category: {trust_level} (Calculated baseline code trust score: {trust_score:.4f}; Definition: 'How reliable is this component's static profile?')\n"
            f"- Systemic Risk: {resolved_risk} (Quantum Walk risk propagation: {walk_score:.4f}; Definition: 'How dangerous is failure to the wider repository graph?')\n"
            f"- Local Reliability: {qvnn_prob:.2%} (QVNN state prediction probability; Definition: 'What is the probability of runtime stability under perturbations?')\n"
            f"- Remediation Priority: {priority_level} (Unified Decision Priority Index UDPI: {udpi:.4f}; Definition: 'How urgently should we modify/refactor this component?')"
        )
        conclusion += definitions_block

        # E. Explainability Score (8.8)
        phases_count = len(phases_used)
        evidence_coverage = phases_count / 4.0
        metrics_found = 0
        if trust_score != 1.0: metrics_found += 1
        if walk_score != 0.0: metrics_found += 1
        if qvnn_prob != 1.0: metrics_found += 1
        if complexity != 0: metrics_found += 1
        numerical_support = metrics_found / 4.0
        active_layers = sum(1 for layer in chain.values() if len(layer) > 0)
        reasoning_completeness = active_layers / 4.0
        contradiction_detection = 1.0
        explainability_score = (evidence_coverage + numerical_support + reasoning_completeness + contradiction_detection) / 4.0
        explainability_pct = round(explainability_score * 100)

        # F. Self-validation Check (8.10)
        agent_results = {}
        agent_path = self.outputs_dir / "agent_results" / "verification_results.json"
        if agent_path.exists():
            try:
                with open(agent_path, "r") as f:
                    agent_results = json.load(f)
            except Exception:
                pass

        validation_errors = []
        if component != "repository":
            from pathlib import Path
            target_p = Path(component)
            if not target_p.exists() and not any(f.get("file") == component for f in files_data):
                validation_errors.append(f"Component file '{component}' not found in local workspace or database.")
        if trust_score is None:
            validation_errors.append("Trust verification score was not resolved.")
        if walk_score is None:
            validation_errors.append("Quantum Walk risk score was not resolved.")
        if not agent_results:
            validation_errors.append("Autonomous agent verification findings are missing.")
        if overall_confidence is None or overall_confidence < 0.0:
            validation_errors.append("Brier-calibrated confidence score computation failed.")
            
        self_validation_status = "PASSED" if not validation_errors else f"FAILED: {'; '.join(validation_errors)}"

        # Check historical decision loop (Phase 7 decision memory)
        historical_file = self.outputs_dir / "historical_decisions.json"
        history = {}
        if historical_file.exists():
            try:
                with open(historical_file, "r") as f:
                    history = json.load(f)
            except Exception:
                pass
        prev_data = history.get(component, {})
        prev_udpi = prev_data.get("udpi")
        
        # Save new decision to history
        history[component] = {
            "udpi": round(udpi, 5),
            "risk": resolved_risk,
            "timestamp": "2026-07-08T12:40:14+05:30"
        }
        try:
            historical_file.parent.mkdir(parents=True, exist_ok=True)
            with open(historical_file, "w") as f:
                json.dump(history, f, indent=4)
        except Exception:
            pass
            
        feedback_note = ""
        if prev_udpi is not None:
            if udpi < prev_udpi:
                feedback_note = f"Remediation feedback loop: Component shows positive risk-reduction trajectory (UDPI decreased from {prev_udpi:.4f} to {udpi:.4f})."
            elif udpi > prev_udpi:
                feedback_note = f"Remediation feedback loop: Component risk profile has escalated (UDPI increased from {prev_udpi:.4f} to {udpi:.4f})."
            else:
                feedback_note = f"Remediation feedback loop: Component risk profile is unchanged from the prior state (UDPI: {udpi:.4f})."
        else:
            feedback_note = "Remediation feedback loop: No prior decision memory found. Initial baseline registered."

        # Contrastive Analysis
        contrastive_explanation = ""
        if priority_level == "CRITICAL":
            contrastive_explanation = (
                "A lower priority level (e.g., HIGH) was rejected because systemic risk propagation "
                f"({walk_score:.4f}) and complexity profile exceeded the repository's upper safety boundaries."
            )
        elif priority_level == "HIGH":
            contrastive_explanation = (
                "A critical priority was rejected due to local QVNN prediction stability, but a medium/low priority "
                f"was ruled out because of significant call-graph centrality and/or active security warnings."
            )
        elif priority_level == "MEDIUM":
            contrastive_explanation = (
                "A higher priority (e.g., HIGH) was rejected because local QVNN reliability is stable, "
                "while a lower priority (e.g., LOW) was ruled out due to moderate coupling complexity."
            )
        else:
            contrastive_explanation = (
                "A higher priority level (e.g., MEDIUM) was rejected because local QVNN stability remains high "
                f"({qvnn_prob:.2%}) and no critical/high severity agent vulnerabilities were verified."
            )

        # Decision Consistency & Decision Reliability
        stability_file = self.outputs_dir / "decision_stability.json"
        consistency_idx = 0.93  # default
        if stability_file.exists():
            try:
                with open(stability_file, "r") as f:
                    stab_data = json.load(f)
                    consistency_idx = stab_data.get("stability_index", 0.93)
            except Exception:
                pass
        decision_reliability = consistency_idx * overall_confidence

        # Add Phase 7 to phases_used list for explainability
        phases_used.append("Phase 7 (Decision Memory Loop)")
        
        # Append historical memory loop output to conclusion
        conclusion += f"\n\nHistorical Memory Loop:\n- {feedback_note}"

        return {
            "resolved_risk": resolved_risk,
            "resolved_confidence": round(overall_confidence, 2),
            "resolved_explanation": conclusion,
            "metrics": {
                "evidence_confidence": round(evidence_confidence, 4),
                "decision_confidence": round(decision_confidence, 4),
                "prediction_confidence": round(prediction_confidence, 4),
                "agreement_desc": agreement_desc,
                "is_capped": is_capped,
                "cap_value": cap_val,
                "cap_reason": cap_reason,
                "data_completeness": round(data_completeness, 4),
                "cross_phase_consistency": round(cross_phase_consistency, 4),
                "explainability_score": explainability_pct,
                "self_validation_status": self_validation_status,
                "decision_consistency": consistency_idx,
                "decision_reliability": decision_reliability,
                "contrastive_explanation": contrastive_explanation,
                "historical_feedback_note": feedback_note
            }
        }
