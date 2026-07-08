import json
from pathlib import Path
from typing import Dict, List, Any

class RecommendationEngine:
    """
    Translates repository metrics and priority rankings into prescriptive repair recommendations.
    Uses repository-adaptive thresholds, computes recommendation confidence, and performs trade-off analysis.
    """

    def __init__(self, outputs_dir: str = "outputs"):
        self.outputs_dir = Path(outputs_dir)

    def load_json(self, path: Path) -> Any:
        if path.exists():
            with open(path, "r") as f:
                try:
                    return json.load(f)
                except Exception:
                    return None
        return None

    def generate_recommendations(self, limit: int = 5) -> List[Dict[str, Any]]:
        rankings = self.load_json(self.outputs_dir / "priority_ranking.json") or []
        intelligence = self.load_json(self.outputs_dir / "repository_intelligence.json") or {}
        agent_results = self.load_json(self.outputs_dir / "agent_results" / "verification_results.json") or {}
        
        thresholds = self.load_json(self.outputs_dir / "adaptive_thresholds.json") or {
            "loc_threshold": 250.0,
            "complexity_threshold": 10.0,
            "imports_threshold": 10.0
        }
        loc_thresh = thresholds.get("loc_threshold", 250.0)
        comp_thresh = thresholds.get("complexity_threshold", 10.0)
        imp_thresh = thresholds.get("imports_threshold", 10.0)

        files_map = {f.get("file"): f for f in intelligence.get("files", []) if f.get("file")}
        total_comps = len(files_map) or 1
        impact_analysis = self.load_json(self.outputs_dir / "impact_analysis.json") or {}

        recommendations = []

        for item in rankings[:limit]:
            comp = item.get("component", "")
            udpi = item.get("udpi", 0.0)
            
            if not comp:
                continue

            file_intel = files_map.get(comp, {})
            metrics = file_intel.get("metrics", {})
            complexity = metrics.get("cyclomatic_complexity", 0)
            loc = metrics.get("lines_of_code", 0)

            # Retrieve agent findings for this component
            comp_findings = []
            for category, findings in agent_results.items():
                if not isinstance(findings, list):
                    continue
                for finding in findings:
                    if finding.get("component") == comp or finding.get("component") == f"file:{comp}":
                        comp_findings.append(finding)

            steps = []
            
            # Rule 1: Complexity / Size Checks
            if complexity > comp_thresh:
                func_info = self.find_most_complex_function(comp)
                if func_info:
                    r_text = (
                        f"Reduce high cyclomatic complexity (current: {complexity}) by refactoring function {func_info['function_name']}() "
                        f"which contributes {func_info['complexity']} complexity ({func_info['percentage']}% of file complexity)."
                    )
                else:
                    r_text = f"Reduce high cyclomatic complexity (current: {complexity}) by decomposing large helper methods."
                
                r_conf = min(0.99, 0.70 + 0.29 * (complexity - comp_thresh) / max(1.0, comp_thresh))
                
                # Dynamic metrics
                rel_gain = 0.25
                sec_gain = 0.0
                dep_imp = 0.05
                eng_cost = max(1.0, complexity * 0.4)
                reg_risk = 0.30 if complexity > comp_thresh else 0.15
                dev_eff = max(1.0, complexity * 0.3)
                roi = (rel_gain + sec_gain + dep_imp) / (eng_cost + reg_risk + dev_eff)

                steps.append({
                    "action": r_text,
                    "justification": f"Because: Cyclomatic complexity {complexity} exceeds the adaptive threshold of {comp_thresh:.1f}.",
                    "confidence": round(r_conf, 4),
                    "reliability_gain": rel_gain,
                    "security_gain": sec_gain,
                    "dependency_impact": dep_imp,
                    "engineering_cost": round(eng_cost, 1),
                    "regression_risk": reg_risk,
                    "developer_effort": round(dev_eff, 1),
                    "roi_score": round(roi, 5)
                })
            elif loc > loc_thresh:
                r_conf = min(0.99, 0.70 + 0.29 * (loc - loc_thresh) / max(1.0, loc_thresh))
                
                rel_gain = 0.20
                sec_gain = 0.0
                dep_imp = 0.10
                eng_cost = max(1.0, loc * 0.04)
                reg_risk = 0.25 if loc > loc_thresh else 0.10
                dev_eff = max(1.0, loc * 0.03)
                roi = (rel_gain + sec_gain + dep_imp) / (eng_cost + reg_risk + dev_eff)

                steps.append({
                    "action": f"Deconstruct large module structure ({loc} LOC) into cohesive sub-modules.",
                    "justification": f"Because: Line count ({loc} LOC) exceeds the adaptive threshold of {loc_thresh:.1f}.",
                    "confidence": round(r_conf, 4),
                    "reliability_gain": rel_gain,
                    "security_gain": sec_gain,
                    "dependency_impact": dep_imp,
                    "engineering_cost": round(eng_cost, 1),
                    "regression_risk": reg_risk,
                    "developer_effort": round(dev_eff, 1),
                    "roi_score": round(roi, 5)
                })

            # Rule 2: Dependency / Coupling Checks
            dep_data = file_intel.get("dependencies", {})
            imports_count = len(dep_data.get("imports", []))
            if imports_count > imp_thresh:
                r_conf = min(0.99, 0.70 + 0.29 * (imports_count - imp_thresh) / max(1.0, imp_thresh))
                
                rel_gain = 0.15
                sec_gain = 0.0
                dep_imp = 0.25
                eng_cost = max(1.0, imports_count * 0.5)
                reg_risk = 0.20
                dev_eff = max(1.0, imports_count * 0.4)
                roi = (rel_gain + sec_gain + dep_imp) / (eng_cost + reg_risk + dev_eff)

                steps.append({
                    "action": f"Decouple dependency coupling: reduce the high number of direct imports (current: {imports_count}) using interfaces.",
                    "justification": f"Because: Import count ({imports_count}) exceeds the adaptive threshold of {imp_thresh:.1f}.",
                    "confidence": round(r_conf, 4),
                    "reliability_gain": rel_gain,
                    "security_gain": sec_gain,
                    "dependency_impact": dep_imp,
                    "engineering_cost": round(eng_cost, 1),
                    "regression_risk": reg_risk,
                    "developer_effort": round(dev_eff, 1),
                    "roi_score": round(roi, 5)
                })

            # Rule 3: QVNN Predictor Flag
            qvnn_prob = item.get("metrics", {}).get("qvnn_probability", 1.0)
            if qvnn_prob < 0.80:
                r_conf = min(0.99, 0.70 + 0.29 * (0.80 - qvnn_prob) / 0.80)
                
                rel_gain = 0.35
                sec_gain = 0.0
                dep_imp = 0.05
                eng_cost = 4.0  # Simple test suite addition
                reg_risk = 0.05
                dev_eff = 3.0
                roi = (rel_gain + sec_gain + dep_imp) / (eng_cost + reg_risk + dev_eff)

                steps.append({
                    "action": f"Increase unit testing coverage: QVNN predicts potential instability (reliability expectation: {qvnn_prob:.2%}).",
                    "justification": f"Because: QVNN confidence probability ({qvnn_prob:.2%}) is below the reliability benchmark of 80.0%.",
                    "confidence": round(r_conf, 4),
                    "reliability_gain": rel_gain,
                    "security_gain": sec_gain,
                    "dependency_impact": dep_imp,
                    "engineering_cost": round(eng_cost, 1),
                    "regression_risk": reg_risk,
                    "developer_effort": round(dev_eff, 1),
                    "roi_score": round(roi, 5)
                })

            # Rule 4: Agent Audit Alerts
            high_severity_alerts = [f for f in comp_findings if f.get("severity") in ["HIGH", "CRITICAL"]]
            if high_severity_alerts:
                rel_gain = 0.20
                sec_gain = 0.40
                dep_imp = 0.10
                eng_cost = len(high_severity_alerts) * 3.5
                reg_risk = 0.15
                dev_eff = len(high_severity_alerts) * 3.0
                roi = (rel_gain + sec_gain + dep_imp) / (eng_cost + reg_risk + dev_eff)

                steps.append({
                    "action": f"Remediate {len(high_severity_alerts)} critical/high security and verification agent findings.",
                    "justification": f"Because: Autonomous verification agents reported {len(high_severity_alerts)} high/critical risk severities during audits.",
                    "confidence": 0.95,
                    "reliability_gain": rel_gain,
                    "security_gain": sec_gain,
                    "dependency_impact": dep_imp,
                    "engineering_cost": round(eng_cost, 1),
                    "regression_risk": reg_risk,
                    "developer_effort": round(dev_eff, 1),
                    "roi_score": round(roi, 5)
                })

            if not steps:
                rel_gain = 0.05
                sec_gain = 0.0
                dep_imp = 0.0
                eng_cost = 2.0
                reg_risk = 0.02
                dev_eff = 2.0
                roi = (rel_gain + sec_gain + dep_imp) / (eng_cost + reg_risk + dev_eff)

                steps.append({
                    "action": "Conduct a manual walkthrough and supplement assertion coverage to improve general code health.",
                    "justification": "Because: Component is highly prioritized by QAOA under resource bounds but does not trigger metric thresholds.",
                    "confidence": 0.75,
                    "reliability_gain": rel_gain,
                    "security_gain": sec_gain,
                    "dependency_impact": dep_imp,
                    "engineering_cost": round(eng_cost, 1),
                    "regression_risk": reg_risk,
                    "developer_effort": round(dev_eff, 1),
                    "roi_score": round(roi, 5)
                })

            # 5. Dynamic Recommendation Ranking (8.4): Sort steps by ROI score descending
            steps.sort(key=lambda x: x.get("roi_score", 0.0), reverse=True)

            # 6. Better Trade-off Analysis (8.7)
            total_hours = sum(s.get("engineering_cost", 0.0) for s in steps)
            total_gain = sum(s.get("reliability_gain", 0.0) for s in steps)
            risk_reduction = max(0.0, udpi - 0.10)
            overall_roi = (total_gain + risk_reduction) / max(1.0, total_hours)

            transitive_count = impact_analysis.get(comp, {}).get("transitive_count", 0)
            blast_ratio = transitive_count / total_comps

            recommendations.append({
                "component": comp,
                "udpi": udpi,
                "priority_rank": item.get("priority_rank", 1),
                "expected_reliability_gain": item.get("expected_reliability_gain", "LOW"),
                "remediations": steps,
                "trade_off_analysis": {
                    "estimated_hours": round(total_hours, 1),
                    "expected_reliability_gain": f"+{total_gain:.1%}",
                    "risk_reduction_delta": round(risk_reduction, 4),
                    "roi_score": round(overall_roi, 5),
                    "blast_radius_impact_ratio": f"{blast_ratio:.2%}"
                },
                "details": {
                    "complexity": complexity,
                    "lines_of_code": loc,
                    "imports_count": imports_count,
                    "findings_count": len(comp_findings)
                }
            })

        output_file = self.outputs_dir / "repair_recommendations.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(recommendations, f, indent=4)

        return recommendations

    def find_most_complex_function(self, file_path: str) -> dict:
        from pathlib import Path
        import ast
        from quest.intelligence.code_metrics import ComplexityVisitor
        
        path = Path(file_path)
        if not path.exists():
            return None
            
        try:
            source = path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
            
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            if not functions:
                return None
                
            max_comp = -1
            max_func = None
            total_complexity = 0
            
            for func in functions:
                visitor = ComplexityVisitor()
                visitor.visit(func)
                total_complexity += visitor.complexity
                if visitor.complexity > max_comp:
                    max_comp = visitor.complexity
                    max_func = func.name
                    
            if max_func:
                pct = (max_comp / max(1, total_complexity)) * 100
                return {
                    "function_name": max_func,
                    "complexity": max_comp,
                    "percentage": round(pct, 1)
                }
        except Exception:
            pass
        return None
