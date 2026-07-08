import json
from pathlib import Path
from typing import Dict, List, Any
import random

class PriorityRanker:
    """
    Ranks repository components using a Unified Decision Priority Index (UDPI) and adaptive thresholds.
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

    def normalize_component_name(self, name: str) -> str:
        name = name.strip()
        if name.startswith("file:"):
            name = name[5:]
        return name

    # Pure Python statistics helpers
    def mean(self, lst: List[float]) -> float:
        return sum(lst) / len(lst) if lst else 0.0

    def variance(self, lst: List[float]) -> float:
        if not lst:
            return 0.0
        m = self.mean(lst)
        return sum((x - m) ** 2 for x in lst) / len(lst)

    def std(self, lst: List[float]) -> float:
        return self.variance(lst) ** 0.5

    def percentile(self, lst: List[float], p: float) -> float:
        if not lst:
            return 0.0
        sorted_lst = sorted(lst)
        k = (len(sorted_lst) - 1) * p
        f = int(k)
        c = f + 1
        if c < len(sorted_lst):
            return sorted_lst[f] + (sorted_lst[c] - sorted_lst[f]) * (k - f)
        return sorted_lst[f]

    def get_percentile_rank(self, val: float, all_vals: List[float]) -> float:
        if not all_vals:
            return 0.0
        less_than = sum(1 for x in all_vals if x < val)
        equal_to = sum(1 for x in all_vals if x == val)
        return (less_than + 0.5 * equal_to) / len(all_vals)

    def calculate_priority_rankings(self) -> List[Dict[str, Any]]:
        # Load inputs
        trust_vectors = self.load_json(self.outputs_dir / "trust_vectors.json") or []
        qaoa_results = self.load_json(self.outputs_dir / "quantum_results" / "qaoa_results.json") or []
        quantum_walk_results = self.load_json(self.outputs_dir / "quantum_results" / "quantum_walk_results.json") or []
        qvnn_results = self.load_json(self.outputs_dir / "quantum_results" / "qvnn_results.json") or []
        agent_results = self.load_json(self.outputs_dir / "agent_results" / "verification_results.json") or {}
        intelligence = self.load_json(self.outputs_dir / "repository_intelligence.json") or {}

        # 1. Compute Repository-Adaptive Thresholds
        files_data = intelligence.get("files", [])
        locs = []
        complexities = []
        import_counts = []

        for file_report in files_data:
            metrics = file_report.get("metrics", {})
            locs.append(metrics.get("lines_of_code", 0))
            complexities.append(metrics.get("cyclomatic_complexity", 0))
            
            dependencies = file_report.get("dependencies", {})
            import_counts.append(len(dependencies.get("imports", [])))

        loc_threshold = self.mean(locs) + self.std(locs)
        complexity_threshold = max(5.0, self.percentile(complexities, 0.90))
        imports_threshold = max(5.0, self.percentile(import_counts, 0.90))

        thresholds = {
            "loc_threshold": round(loc_threshold, 2),
            "complexity_threshold": round(complexity_threshold, 2),
            "imports_threshold": round(imports_threshold, 2)
        }
        with open(self.outputs_dir / "adaptive_thresholds.json", "w") as f:
            json.dump(thresholds, f, indent=4)

        # 2. Build Dependency Centrality and Component Mappings
        all_components = [file_report.get("file", "") for file_report in files_data if file_report.get("file")]
        total_comps = len(all_components) or 1
        
        imports_graph = {comp: set() for comp in all_components}
        incoming_graph = {comp: set() for comp in all_components}

        for file_report in files_data:
            comp = file_report.get("file", "")
            if not comp:
                continue
            imports_list = file_report.get("dependencies", {}).get("imports", [])
            for imp in imports_list:
                imp_clean = imp.replace(".", "/")
                for c in all_components:
                    c_no_ext = str(Path(c).with_suffix(""))
                    if c_no_ext.endswith(imp_clean) or imp_clean.endswith(c_no_ext) or imp_clean in c_no_ext:
                        if c != comp:
                            imports_graph[comp].add(c)
                            incoming_graph[c].add(comp)

        components = {}

        # 3. Integrate Trust Scores
        for item in trust_vectors:
            path = self.normalize_component_name(item.get("file_path", ""))
            if not path:
                continue
            if path not in components:
                components[path] = self.init_component_metrics(path)
            components[path]["trust_score"] = item.get("trust_score", 1.0)
            components[path]["trust_category"] = item.get("trust_category", "UNKNOWN")

        # 4. Integrate QAOA Priorities
        for item in qaoa_results:
            path = self.normalize_component_name(item.get("component", ""))
            if not path:
                continue
            if path not in components:
                components[path] = self.init_component_metrics(path)
            components[path]["qaoa_priority_score"] = item.get("priority_score", 0.0)
            components[path]["qaoa_rank"] = item.get("quantum_priority_rank")

        # 5. Integrate Quantum Walk Propagation Scores
        for item in quantum_walk_results:
            source = self.normalize_component_name(item.get("source_component", ""))
            if not source:
                continue
            if source not in components:
                components[source] = self.init_component_metrics(source)
            scores = item.get("propagation_scores", {})
            self_score = scores.get(f"file:{source}", scores.get(source, 0.0))
            max_other = max([v for k, v in scores.items() if k != source and k != f"file:{source}"], default=0.0)
            components[source]["quantum_walk_score"] = max(self_score, max_other)

        # 6. Integrate QVNN Predictor Expected State
        for item in qvnn_results:
            path = self.normalize_component_name(item.get("component", ""))
            if not path:
                continue
            if path not in components:
                components[path] = self.init_component_metrics(path)
            components[path]["qvnn_probability"] = item.get("reliability_probability", 1.0)
            components[path]["qvnn_state"] = item.get("predicted_state", "HIGH_RELIABILITY")

        # 7. Integrate Agent Severity
        severity_values = {"INFO": 0.0, "LOW": 0.25, "MEDIUM": 0.5, "HIGH": 0.75, "CRITICAL": 1.0}
        for category, findings in agent_results.items():
            if not isinstance(findings, list):
                continue
            for finding in findings:
                path = self.normalize_component_name(finding.get("component", ""))
                if not path:
                    continue
                if path not in components:
                    components[path] = self.init_component_metrics(path)
                
                sev = finding.get("severity", "INFO")
                sev_val = severity_values.get(sev, 0.0)
                components[path]["agent_severities"].append(sev_val)

        # 8. Integrate Complexity and Dependency Centrality
        for file_report in files_data:
            path = file_report.get("file", "")
            if not path or path not in components:
                continue
            comp_complexity = file_report.get("metrics", {}).get("cyclomatic_complexity", 0)
            components[path]["complexity"] = comp_complexity
            components[path]["lines_of_code"] = file_report.get("metrics", {}).get("lines_of_code", 0)

            in_deg = len(incoming_graph.get(path, set()))
            out_deg = len(imports_graph.get(path, set()))
            denom = max(1, total_comps - 1)
            components[path]["dependency_centrality"] = (in_deg + out_deg) / denom

        # Ensure all components have entries initialized
        for path in all_components:
            if path not in components:
                components[path] = self.init_component_metrics(path)

        # 9. Compute Adaptive Weights based on Variance & Quality & Context (8.1)
        max_cx = max([c["complexity"] for c in components.values()]) if components else 1.0
        if max_cx <= 0:
            max_cx = 1.0

        trust_scores_list = [1.0 - c["trust_score"] for c in components.values()]
        walk_scores_list = [c["quantum_walk_score"] for c in components.values()]
        qaoa_scores_list = [c["qaoa_priority_score"] for c in components.values()]
        qvnn_scores_list = [1.0 - c["qvnn_probability"] for c in components.values()]
        agent_scores_list = [sum(c["agent_severities"])/len(c["agent_severities"]) if c["agent_severities"] else 0.0 for c in components.values()]
        centralities_list = [c["dependency_centrality"] for c in components.values()]
        complexities_list = [c["complexity"] / max_cx for c in components.values()]

        # Compute variances (variance helper adds small constant to ensure all weights are > 0)
        var_t = max(0.01, self.variance(trust_scores_list))
        var_w = max(0.01, self.variance(walk_scores_list))
        var_q = max(0.01, self.variance(qaoa_scores_list))
        var_v = max(0.01, self.variance(qvnn_scores_list))
        var_a = max(0.01, self.variance(agent_scores_list))
        var_c = max(0.01, self.variance(centralities_list))
        var_cx = max(0.01, self.variance(complexities_list))

        # Evidence quality metrics
        eq_t = 1.0 if trust_vectors else 0.1
        eq_w = 1.0 if quantum_walk_results else 0.1
        eq_q = 1.0 if qaoa_results else 0.1
        eq_v = 1.0 if qvnn_results else 0.1
        eq_a = len(agent_results) / 4.0 if agent_results else 0.1
        eq_c = 1.0
        eq_cx = 1.0

        # Prediction confidence metrics
        pc_t = 1.0
        pc_w = 0.90
        pc_q = 0.85
        pc_v = self.mean([c["qvnn_probability"] for c in components.values()]) if qvnn_results else 0.80
        pc_a = 0.85
        pc_c = 1.0
        pc_cx = 1.0

        # Repository contexts
        rc_t = 1.0
        rc_w = 1.0 + self.mean(centralities_list)
        rc_q = 1.0
        rc_v = 1.0
        rc_a = 1.0
        rc_c = 1.0 + self.mean(centralities_list)
        rc_cx = 1.0 + (self.mean(complexities_list) / 100.0)

        # Raw weights calculation
        raw_w_t = var_t * eq_t * pc_t * rc_t
        raw_w_w = var_w * eq_w * pc_w * rc_w
        raw_w_q = var_q * eq_q * pc_q * rc_q
        raw_w_v = var_v * eq_v * pc_v * rc_v
        raw_w_a = var_a * eq_a * pc_a * rc_a
        raw_w_c = var_c * eq_c * pc_c * rc_c
        raw_w_cx = var_cx * eq_cx * pc_cx * rc_cx

        sum_raw = raw_w_t + raw_w_w + raw_w_q + raw_w_v + raw_w_a + raw_w_c + raw_w_cx
        if sum_raw == 0:
            sum_raw = 1.0

        weights = {
            "trust": raw_w_t / sum_raw,
            "quantum_walk": raw_w_w / sum_raw,
            "qaoa": raw_w_q / sum_raw,
            "qvnn": raw_w_v / sum_raw,
            "agents": raw_w_a / sum_raw,
            "dependency_centrality": raw_w_c / sum_raw,
            "complexity": raw_w_cx / sum_raw
        }

        # Enforce minimum weight threshold of 0.05 to prevent 0.0% output representation
        for k in weights:
            weights[k] = max(0.05, weights[k])
            
        s_w = sum(weights.values())
        weights = {k: round(v / s_w, 4) for k, v in weights.items()}

        # Normalize weights so they sum exactly to 1.0 (adjust complexity)
        diff = round(1.0 - sum(weights.values()), 4)
        weights["complexity"] = round(weights["complexity"] + diff, 4)

        # Save adaptive weights
        weights_file = self.outputs_dir / "weights.json"
        weights_file.parent.mkdir(parents=True, exist_ok=True)
        with open(weights_file, "w") as f:
            json.dump(weights, f, indent=4)

        # 10. Perform Repository-aware Trust Calibration & Factor Resolution using Percentile Ranks (8.3)
        rankings = []
        for path, data in components.items():
            t_factor = self.get_percentile_rank(1.0 - data["trust_score"], trust_scores_list)
            w_factor = self.get_percentile_rank(data["quantum_walk_score"], walk_scores_list)
            q_factor = self.get_percentile_rank(data["qaoa_priority_score"], qaoa_scores_list)
            v_factor = self.get_percentile_rank(1.0 - data["qvnn_probability"], qvnn_scores_list)
            
            a_val = sum(data["agent_severities"])/len(data["agent_severities"]) if data["agent_severities"] else 0.0
            a_factor = self.get_percentile_rank(a_val, agent_scores_list)
            
            c_factor = self.get_percentile_rank(data["dependency_centrality"], centralities_list)
            cx_factor = self.get_percentile_rank(data["complexity"], complexities_list)

            # Weighted UDPI calculation
            udpi = (
                weights["trust"] * t_factor +
                weights["quantum_walk"] * w_factor +
                weights["qaoa"] * q_factor +
                weights["qvnn"] * v_factor +
                weights["agents"] * a_factor +
                weights["dependency_centrality"] * c_factor +
                weights["complexity"] * cx_factor
            )

            total_sum = udpi if udpi > 0 else 1e-5
            contributors = {
                "trust": round((weights["trust"] * t_factor) / total_sum, 4),
                "quantum_walk": round((weights["quantum_walk"] * w_factor) / total_sum, 4),
                "qaoa": round((weights["qaoa"] * q_factor) / total_sum, 4),
                "qvnn": round((weights["qvnn"] * v_factor) / total_sum, 4),
                "agents": round((weights["agents"] * a_factor) / total_sum, 4),
                "dependency_centrality": round((weights["dependency_centrality"] * c_factor) / total_sum, 4),
                "complexity": round((weights["complexity"] * cx_factor) / total_sum, 4)
            }

            if udpi > 0.6:
                gain = "CRITICAL"
            elif udpi > 0.4:
                gain = "HIGH"
            elif udpi > 0.2:
                gain = "MEDIUM"
            else:
                gain = "LOW"

            rankings.append({
                "component": path,
                "udpi": round(udpi, 5),
                "expected_reliability_gain": gain,
                "priority_rank": 0,
                "udpi_contributors": contributors,
                "metrics": {
                    "component_risk": round(0.5 * cx_factor + 0.5 * a_factor, 4),
                    "propagation_risk": round(w_factor, 4),
                    "reliability_score": round(1.0 - (0.5 * t_factor + 0.5 * v_factor), 4),
                    "importance_score": round(0.5 * c_factor + 0.5 * q_factor, 4),
                    "maintenance_priority": round(udpi, 4),
                    "trust_score": round(data["trust_score"], 4),
                    "quantum_walk_score": round(data["quantum_walk_score"], 4),
                    "qaoa_rank": data["qaoa_rank"],
                    "qvnn_probability": round(data["qvnn_probability"], 4),
                    "avg_agent_severity": round(a_val, 4),
                    "dependency_centrality": round(data["dependency_centrality"], 4),
                    "complexity": data["complexity"],
                    "lines_of_code": data["lines_of_code"]
                }
            })

        # Sort and Rank
        rankings = sorted(rankings, key=lambda x: x["udpi"], reverse=True)
        for idx, item in enumerate(rankings):
            item["priority_rank"] = idx + 1

        output_file = self.outputs_dir / "priority_ranking.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(rankings, f, indent=4)

        # 11. Run Stability Analysis under Schrödinger Perturbations (8.5)
        base_top3 = [item["component"] for item in rankings[:3]]
        stability_matches = 0
        trials = 100
        
        # Seed perturbation for deterministic tests reproducibility
        random.seed(42)

        for _ in range(trials):
            perturbed_scores = []
            for path, data in components.items():
                p_t = max(0.0, min(1.0, (1.0 - data["trust_score"]) * random.uniform(0.95, 1.05)))
                p_w = max(0.0, min(1.0, data["quantum_walk_score"] * random.uniform(0.95, 1.05)))
                p_q = max(0.0, min(1.0, data["qaoa_priority_score"] * random.uniform(0.95, 1.05)))
                p_v = max(0.0, min(1.0, (1.0 - data["qvnn_probability"]) * random.uniform(0.95, 1.05)))
                
                a_val = sum(data["agent_severities"])/len(data["agent_severities"]) if data["agent_severities"] else 0.0
                p_a = max(0.0, min(1.0, a_val * random.uniform(0.95, 1.05)))
                
                p_c = max(0.0, min(1.0, data["dependency_centrality"] * random.uniform(0.95, 1.05)))
                p_cx = max(0.0, min(1.0, (data["complexity"] / (max(complexities_list) or 1.0)) * random.uniform(0.95, 1.05)))

                perturbed_udpi = (
                    weights["trust"] * p_t +
                    weights["quantum_walk"] * p_w +
                    weights["qaoa"] * p_q +
                    weights["qvnn"] * p_v +
                    weights["agents"] * p_a +
                    weights["dependency_centrality"] * p_c +
                    weights["complexity"] * p_cx
                )
                perturbed_scores.append((path, perturbed_udpi))

            perturbed_scores.sort(key=lambda x: x[1], reverse=True)
            perturbed_top3 = [item[0] for item in perturbed_scores[:3]]
            
            if set(perturbed_top3) == set(base_top3):
                stability_matches += 1

        stability_index = stability_matches / trials
        stability_cohort = "VERY HIGH" if stability_index >= 0.90 else "HIGH" if stability_index >= 0.75 else "MODERATE" if stability_index >= 0.50 else "LOW"

        stability_report = {
            "stability_index": stability_index,
            "stability_cohort": stability_cohort,
            "trials_run": trials,
            "perturbation_range": "+/- 5%"
        }
        with open(self.outputs_dir / "decision_stability.json", "w") as f:
            json.dump(stability_report, f, indent=4)

        # 12. Run Sensitivity Analysis (8.9)
        base_order = [item["component"] for item in rankings]
        sensitivity_report = {}
        
        for w_name, w_val in weights.items():
            perturbed_weights_pos = weights.copy()
            perturbed_weights_pos[w_name] = w_val * 1.10
            total_w = sum(perturbed_weights_pos.values()) or 1.0
            perturbed_weights_pos = {k: v / total_w for k, v in perturbed_weights_pos.items()}
            
            perturbed_rankings = []
            for path, data in components.items():
                t_f = self.get_percentile_rank(1.0 - data["trust_score"], trust_scores_list)
                w_f = self.get_percentile_rank(data["quantum_walk_score"], walk_scores_list)
                q_f = self.get_percentile_rank(data["qaoa_priority_score"], qaoa_scores_list)
                v_f = self.get_percentile_rank(1.0 - data["qvnn_probability"], qvnn_scores_list)
                a_val = sum(data["agent_severities"])/len(data["agent_severities"]) if data["agent_severities"] else 0.0
                a_f = self.get_percentile_rank(a_val, agent_scores_list)
                c_f = self.get_percentile_rank(data["dependency_centrality"], centralities_list)
                cx_f = self.get_percentile_rank(data["complexity"], complexities_list)
                
                udpi_p = (
                    perturbed_weights_pos["trust"] * t_f +
                    perturbed_weights_pos["quantum_walk"] * w_f +
                    perturbed_weights_pos["qaoa"] * q_f +
                    perturbed_weights_pos["qvnn"] * v_f +
                    perturbed_weights_pos["agents"] * a_f +
                    perturbed_weights_pos["dependency_centrality"] * c_f +
                    perturbed_weights_pos["complexity"] * cx_f
                )
                perturbed_rankings.append((path, udpi_p))
            
            perturbed_rankings = sorted(perturbed_rankings, key=lambda x: x[1], reverse=True)
            perturbed_order = [item[0] for item in perturbed_rankings]
            
            tau = self.calculate_kendall_tau(base_order, perturbed_order)
            # Find feature contribution (relative change delta)
            sensitivity_report[w_name] = {
                "weight_value": w_val,
                "kendall_tau_perturbation": round(tau, 4),
                "robustness": "HIGH" if tau >= 0.90 else "MODERATE" if tau >= 0.75 else "SENSITIVE"
            }
            
        with open(self.outputs_dir / "weights_sensitivity_report.json", "w") as f:
            json.dump(sensitivity_report, f, indent=4)

        return rankings

    def calculate_kendall_tau(self, r1: List[str], r2: List[str]) -> float:
        n = len(r1)
        if n <= 1:
            return 1.0
        pos2 = {comp: idx for idx, comp in enumerate(r2)}
        concordant = 0
        discordant = 0
        for i in range(n):
            for j in range(i + 1, n):
                c1, c2 = r1[i], r1[j]
                if c1 in pos2 and c2 in pos2:
                    if pos2[c1] < pos2[c2]:
                        concordant += 1
                    else:
                        discordant += 1
        total_pairs = concordant + discordant
        if total_pairs == 0:
            return 1.0
        return (concordant - discordant) / total_pairs

    def init_component_metrics(self, path: str) -> Dict[str, Any]:
        return {
            "component": path,
            "trust_score": 1.0,
            "trust_category": "UNKNOWN",
            "qaoa_priority_score": 0.0,
            "qaoa_rank": None,
            "quantum_walk_score": 0.0,
            "qvnn_probability": 1.0,
            "qvnn_state": "HIGH_RELIABILITY",
            "agent_severities": [],
            "complexity": 0,
            "lines_of_code": 0,
            "dependency_centrality": 0.0
        }
