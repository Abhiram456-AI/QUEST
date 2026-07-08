import json
from pathlib import Path
from typing import Dict, List, Any

class ScenarioSimulator:
    """
    Simulates the quantitative impact of refactoring components on repository-wide reliability.
    Computes simulated changes dynamically based on structural metrics and models.
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

    def simulate_refactoring(
        self,
        target_component: str,
        loc_reduction: float = 0.40,
        complexity_reduction: float = 0.45,
        coupling_reduction: float = 0.30
    ) -> Dict[str, Any]:
        # Load baseline files
        trust_vectors = self.load_json(self.outputs_dir / "trust_vectors.json") or []
        qvnn_results = self.load_json(self.outputs_dir / "quantum_results" / "qvnn_results.json") or []
        quantum_walk_results = self.load_json(self.outputs_dir / "quantum_results" / "quantum_walk_results.json") or []
        intelligence = self.load_json(self.outputs_dir / "repository_intelligence.json") or {}

        # Find target component path
        target_clean = target_component.strip()
        if target_clean.startswith("file:"):
            target_clean = target_clean[5:]

        all_paths = [t.get("file_path") for t in trust_vectors if t.get("file_path")]
        
        if target_clean not in all_paths:
            target_clean_lower = target_clean.replace("\\", "/").lower()
            matches = []
            for p in all_paths:
                p_lower = p.replace("\\", "/").lower()
                p_filename = p_lower.split("/")[-1]
                target_filename = target_clean_lower.split("/")[-1]
                if p_filename == target_filename:
                    is_test = "test_" in p_lower or "/tests/" in p_lower
                    matches.append((0 if not is_test else 1, len(p_lower), p))
                elif target_clean_lower in p_lower:
                    is_test = "test_" in p_lower or "/tests/" in p_lower
                    matches.append((2 if not is_test else 3, len(p_lower), p))
                elif p_lower in target_clean_lower:
                    is_test = "test_" in p_lower or "/tests/" in p_lower
                    matches.append((4 if not is_test else 5, len(p_lower), p))
            if matches:
                matches.sort(key=lambda x: (x[0], x[1]))
                target_clean = matches[0][2]

        if target_clean not in all_paths:
            return {"error": f"Component {target_component} not found for simulation."}

        # 1. Load Baseline Metrics from Repository Intelligence
        files_map = {f.get("file"): f for f in intelligence.get("files", []) if f.get("file")}
        file_intel = files_map.get(target_clean, {})
        metrics = file_intel.get("metrics", {})
        
        base_complexity = metrics.get("cyclomatic_complexity", 1)
        base_loc = metrics.get("lines_of_code", 10)
        
        dep_data = file_intel.get("dependencies", {})
        base_imports = len(dep_data.get("imports", []))

        # Max values in repository for scaling
        all_complexities = [f.get("metrics", {}).get("cyclomatic_complexity", 1) for f in files_map.values()]
        max_complexity = max(all_complexities) if all_complexities else 1.0

        all_imports = [len(f.get("dependencies", {}).get("imports", [])) for f in files_map.values()]
        max_imports = max(all_imports) if all_imports else 1.0

        # Load baseline trust
        base_trust = 1.0
        base_vector = [0.0, 0.0, 0.0, 1.0]
        for t in trust_vectors:
            if t.get("file_path") == target_clean:
                base_trust = t.get("trust_score", 1.0)
                base_vector = t.get("vector", [0.0, 0.0, 0.0, 1.0])
                break

        base_walk = 0.0
        for item in quantum_walk_results:
            source = item.get("source_component", "")
            if source == target_clean or source == f"file:{target_clean}":
                scores = item.get("propagation_scores", {})
                base_walk = scores.get(f"file:{target_clean}", scores.get(target_clean, 0.0))
                break

        base_qvnn_prob = 1.0
        for q in qvnn_results:
            if q.get("component") == target_clean:
                base_qvnn_prob = q.get("reliability_probability", 1.0)
                break

        # 2. Compute Simulated Improvements
        sim_loc = int(base_loc * (1.0 - loc_reduction))
        sim_complexity = max(1, int(base_complexity * (1.0 - complexity_reduction)))
        sim_imports = int(base_imports * (1.0 - coupling_reduction))

        # Scale back to trust vector format: [complexity_ratio, dependency_coupling_ratio, security, reliability]
        sim_complexity_ratio = round(base_vector[0] * (1.0 - complexity_reduction), 4)
        sim_coupling_ratio = round(base_vector[1] * (1.0 - coupling_reduction), 4)
        
        # Security profile is preserved; reliability improves to 0.95
        sim_reliability = 0.95
        sim_vector = [sim_complexity_ratio, sim_coupling_ratio, base_vector[2], sim_reliability]

        # Recompute trust score: 1.0 - mean(complexity, coupling, security, 1.0 - reliability)
        sim_trust = round(1.0 - (sim_vector[0] + sim_vector[1] + sim_vector[2] + (1.0 - sim_vector[3])) / 4.0, 5)

        # Recalculate quantum walk score: centrality/propagation reduces quadratically with imports reduction
        sim_walk = round(base_walk * ((1.0 - coupling_reduction) ** 2), 5)

        # 3. Calculate Repository-Wide Delta via 1000 Monte Carlo trials
        import numpy as np
        num_trials = 1000
        np.random.seed(42)  # For reproducibility

        all_base_probs = [q.get("reliability_probability", 1.0) for q in qvnn_results]
        base_repo_reliability = sum(all_base_probs) / len(all_base_probs) if all_base_probs else 1.0

        sum_other_qvnn = sum([q.get("reliability_probability", 1.0) for q in qvnn_results if q.get("component") != target_clean])
        total_comps = len(qvnn_results) if qvnn_results else 1

        trials = []
        for _ in range(num_trials):
            r_loc_red = max(0.0, min(0.95, loc_reduction + np.random.normal(0, 0.08)))
            r_comp_red = max(0.0, min(0.95, complexity_reduction + np.random.normal(0, 0.08)))
            r_coup_red = max(0.0, min(0.95, coupling_reduction + np.random.normal(0, 0.08)))
            
            t_comp_ratio = base_vector[0] * (1.0 - r_comp_red)
            t_coup_ratio = base_vector[1] * (1.0 - r_coup_red)
            t_vector = [t_comp_ratio, t_coup_ratio, base_vector[2], 0.95]
            
            t_trust = 1.0 - (t_vector[0] + t_vector[1] + t_vector[2] + (1.0 - t_vector[3])) / 4.0
            
            t_qvnn = min(0.99, max(0.2, base_qvnn_prob + (t_trust - base_trust) * 0.35 + np.random.normal(0, 0.04)))
            t_repo = (sum_other_qvnn + t_qvnn) / total_comps
            trials.append(t_repo)

        sim_repo_reliability = float(np.mean(trials))
        best_repo_reliability = float(np.max(trials))
        worst_repo_reliability = float(np.min(trials))
        std_trial = float(np.std(trials))
        sem = std_trial / (num_trials ** 0.5)
        
        ci_lower = sim_repo_reliability - 1.96 * std_trial
        ci_upper = sim_repo_reliability + 1.96 * std_trial
        
        diffs = [x - sim_repo_reliability for x in trials]
        skewness = float(np.mean([d**3 for d in diffs]) / (std_trial**3)) if std_trial > 0 else 0.0
        kurtosis = float(np.mean([d**4 for d in diffs]) / (std_trial**4)) - 3.0 if std_trial > 0 else 0.0

        delta_reliability = sim_repo_reliability - base_repo_reliability
        pct_improvement = (delta_reliability / base_repo_reliability) * 100.0 if base_repo_reliability > 0 else 0.0
        best_pct = ((best_repo_reliability - base_repo_reliability) / base_repo_reliability) * 100.0 if base_repo_reliability > 0 else 0.0
        worst_pct = ((worst_repo_reliability - base_repo_reliability) / base_repo_reliability) * 100.0 if base_repo_reliability > 0 else 0.0

        # Construct explanation
        base_explanation = (
            f"Refactoring {target_clean} is simulated via 1000 Monte Carlo trials to increase the repository's overall quantum reliability index "
            f"by +{pct_improvement:.2f}% expected (ranging from +{worst_pct:.2f}% worst-case to +{best_pct:.2f}% best-case). "
            f"This is driven by reducing structural complexity T[0] from {base_vector[0]:.2f} to {sim_complexity_ratio:.2f} "
            f"and minimizing call-graph risk propagation bottleneck values by {1.0 - (sim_walk / max(1e-5, base_walk)):.1%}."
        )
        if base_repo_reliability > 0.80:
            base_explanation += (
                f"\nNote: The repository baseline reliability is already high ({base_repo_reliability:.2%}), "
                "so improvements are naturally incremental and represent highly stable marginal gains."
            )

        assumptions_str = (
            f"Computed simulation: sampled via 1000 Monte Carlo regression trials. "
            f"LOC reduction: sampled with mean {loc_reduction:.0%} (std dev: 8%). "
            f"Complexity reduction: sampled with mean {complexity_reduction:.0%} (std dev: 8%). "
            f"Coupling reduction: sampled with mean {coupling_reduction:.0%} (std dev: 8%), "
            "while leaving repository topology unchanged (Confidence interval: 95%)."
        )

        simulation_result = {
            "type": "simulation",
            "not_observed": True,
            "simulated_component": target_clean,
            "simulation_assumptions": assumptions_str,
            "simulation_metadata": {
                "simulation_type": "Monte Carlo Regression",
                "trials": 1000,
                "random_variables": [
                    "complexity reduction",
                    "dependency reduction",
                    "trust recalculation"
                ],
                "seed": 42
            },
            "assumptions": [
                f"LOC reduction: {loc_reduction:.0%}",
                f"Complexity reduction: {complexity_reduction:.0%}",
                f"Coupling reduction: {coupling_reduction:.0%}"
            ],
            "baseline_observed": {
                "trust_score": round(base_trust, 5),
                "trust_vector": base_vector,
                "quantum_walk_score": round(base_walk, 5),
                "qvnn_reliability_probability": round(base_qvnn_prob, 5)
            },
            "simulated_counterfactual": {
                "trust_score": round(sim_trust, 5),
                "trust_vector": sim_vector,
                "quantum_walk_score": round(sim_walk, 5),
                "qvnn_reliability_probability": round(sim_repo_reliability, 5)
            },
            "repository_impact": {
                "baseline_reliability_index": round(base_repo_reliability, 5),
                "simulated_reliability_index": round(sim_repo_reliability, 5),
                "best_case_reliability_index": round(best_repo_reliability, 5),
                "worst_case_reliability_index": round(worst_repo_reliability, 5),
                "delta": round(delta_reliability, 5),
                "percentage_improvement": round(pct_improvement, 2),
                "best_case_percentage_improvement": round(best_pct, 2),
                "worst_case_percentage_improvement": round(worst_pct, 2),
                "standard_error_mean": round(sem, 6),
                "confidence_interval_95": [round(ci_lower, 5), round(ci_upper, 5)],
                "normality_check": {
                    "skewness": round(skewness, 4),
                    "kurtosis": round(kurtosis, 4),
                    "is_normal": abs(skewness) < 0.5 and abs(kurtosis) < 1.0
                },
                "explanation": base_explanation
            }
        }

        # Save to file
        output_file = self.outputs_dir / "simulation_results.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(simulation_result, f, indent=4)

        return simulation_result
