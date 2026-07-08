import json
from pathlib import Path

class ConfigProvider:
    def __init__(self, outputs_dir: str = "outputs"):
        self.outputs_dir = Path(outputs_dir)
        self.config_path = Path(__file__).parent / "configuration_profile.json"
        self.config = self.load_default_config()

    def load_default_config(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "reliability_benchmark": 0.80,
            "simulation_defaults": {
                "loc_reduction": 0.40,
                "complexity_reduction": 0.45,
                "coupling_reduction": 0.30
            },
            "static_benchmarks": {
                "complexity_threshold": 40
            },
            "weights": {
                "trust": 0.15,
                "quantum_walk": 0.15,
                "qaoa": 0.15,
                "qvnn": 0.15,
                "agents": 0.15,
                "dependency_centrality": 0.15,
                "complexity": 0.10
            },
            "confidence_cappings": {
                "max_confidence": 0.95,
                "disagreement_penalty_ceiling": 0.30
            },
            "adaptive_thresholds": {
                "quantum_walk_dangerous_threshold": 0.50,
                "qvnn_reliable_threshold": 0.70
            }
        }

    def get_weights(self) -> dict:
        return self.config.get("weights", {
            "trust": 0.15,
            "quantum_walk": 0.15,
            "qaoa": 0.15,
            "qvnn": 0.15,
            "agents": 0.15,
            "dependency_centrality": 0.15,
            "complexity": 0.10
        })

    def get_confidence_cappings(self) -> dict:
        return self.config.get("confidence_cappings", {
            "max_confidence": 0.95,
            "disagreement_penalty_ceiling": 0.30
        })

    def get_adaptive_thresholds(self) -> dict:
        return self.config.get("adaptive_thresholds", {
            "quantum_walk_dangerous_threshold": 0.50,
            "qvnn_reliable_threshold": 0.70
        })

    def get_reliability_benchmark(self) -> float:
        return self.config.get("reliability_benchmark", 0.80)

    def get_simulation_defaults(self) -> dict:
        return self.config.get("simulation_defaults", {
            "loc_reduction": 0.40,
            "complexity_reduction": 0.45,
            "coupling_reduction": 0.30
        })

    def get_complexity_threshold(self) -> dict:
        """
        Dynamically computes complexity threshold based on repository percentile calibration.
        """
        repo_intel = self.outputs_dir / "repository_intelligence.json"
        if repo_intel.exists():
            try:
                with open(repo_intel, "r") as f:
                    data = json.load(f)
                complexities = []
                for file_info in data.get("files", []):
                    comp = file_info.get("metrics", {}).get("cyclomatic_complexity")
                    if comp is not None:
                        complexities.append(comp)
                if complexities:
                    # Compute 90th percentile
                    complexities.sort()
                    idx = int(len(complexities) * 0.90)
                    val = max(10, complexities[idx])
                    return {
                        "threshold_source": "repository percentile calibration (90th percentile)",
                        "threshold_value": val,
                        "confidence": 0.92
                    }
            except Exception:
                pass
        
        return {
            "threshold_source": "static profile benchmark",
            "threshold_value": self.config.get("static_benchmarks", {}).get("complexity_threshold", 40),
            "confidence": 0.70
        }
