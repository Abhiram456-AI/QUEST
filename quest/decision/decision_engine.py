import json
from pathlib import Path
from typing import Dict, List, Any

from quest.decision.priority_ranker import PriorityRanker
from quest.decision.impact_analyzer import ImpactAnalyzer
from quest.decision.dependency_reasoner import DependencyReasoner
from quest.decision.recommendation_engine import RecommendationEngine
from quest.decision.scenario_simulator import ScenarioSimulator

class DecisionEngine:
    """
    Orchestration coordinator for QUEST Phase 6 Decision Intelligence.
    Integrates ranking, impact analysis, dependency tracing, recommendations, and simulation.
    Generates structured, auditable reasoning traces separating facts from recommendations.
    """

    def __init__(self, outputs_dir: str = "outputs"):
        self.outputs_dir = Path(outputs_dir)
        self.ranker = PriorityRanker(outputs_dir)
        self.impact_analyzer = ImpactAnalyzer(outputs_dir)
        self.reasoner = DependencyReasoner(outputs_dir)
        self.recommendation_engine = RecommendationEngine(outputs_dir)
        self.simulator = ScenarioSimulator(outputs_dir)

    def execute_decision_pipeline(self) -> Dict[str, Any]:
        """
        Runs the full Phase 6 decision pipeline, generating all report files.
        """
        print("QUEST Phase 6: Decision Intelligence Started")

        # 1. Generate Priority Rankings
        rankings = self.ranker.calculate_priority_rankings()

        # 2. Run Impact Analysis
        impacts = self.impact_analyzer.analyze_impact()

        # 3. Generate Repair Recommendations
        recommendations = self.recommendation_engine.generate_recommendations(limit=5)

        # 4. Generate Default Simulation Results (simulate refactoring the top priority component)
        if rankings:
            top_comp = rankings[0]["component"]
            self.simulator.simulate_refactoring(top_comp)

        # 5. Compile Rich Structured Reasoning Traces (for top 5 components)
        structured_traces = []
        for rec in recommendations:
            comp = rec["component"]
            
            # Find ranking details
            rank_item = None
            for item in rankings:
                if item["component"] == comp:
                    rank_item = item
                    break
            
            if not rank_item:
                continue

            # Load impact data
            comp_impact = impacts.get(comp, {})

            # Separate Observed Facts, Interpretation, Recommendations & Trade-offs
            trace = {
                "component": comp,
                "udpi": rank_item["udpi"],
                "priority_rank": rank_item["priority_rank"],
                "udpi_contributors": rank_item["udpi_contributors"],
                "observed_facts": {
                    "trust_score": rank_item["metrics"]["trust_score"],
                    "complexity": rank_item["metrics"]["complexity"],
                    "quantum_walk_score": rank_item["metrics"]["quantum_walk_score"],
                    "qvnn_probability": rank_item["metrics"]["qvnn_probability"],
                    "dependency_centrality": rank_item["metrics"]["dependency_centrality"],
                    "lines_of_code": rank_item["metrics"]["lines_of_code"]
                },
                "interpretation": {
                    "risk_propagation_rating": comp_impact.get("impact_rating", "LOW"),
                    "reliability_assessment": rank_item["expected_reliability_gain"],
                    "blast_radius_downstream_files_count": comp_impact.get("transitive_count", 0),
                    "critical_path_length": comp_impact.get("critical_path_length", 0),
                    "average_dependency_depth": comp_impact.get("average_dependency_depth", 0.0)
                },
                "recommendations": [
                    {
                        "action": rem["action"],
                        "justification": rem["justification"],
                        "confidence": rem["confidence"]
                    }
                    for rem in rec["remediations"]
                ],
                "trade_off_analysis": rec["trade_off_analysis"]
            }
            structured_traces.append(trace)

        # 6. Build Unified Decision Report
        avg_udpi = sum([item["udpi"] for item in rankings]) / len(rankings) if rankings else 0.0
        critical_count = sum([1 for item in rankings if item["expected_reliability_gain"] == "CRITICAL"])
        high_count = sum([1 for item in rankings if item["expected_reliability_gain"] == "HIGH"])

        report = {
            "summary": {
                "total_analyzed_components": len(rankings),
                "average_udpi": round(avg_udpi, 4),
                "critical_remediation_count": critical_count,
                "high_remediation_count": high_count,
                "recommendation": "Address critical structural bottlenecks immediately to minimize cascading call-graph risks."
            },
            "structured_reasoning_traces": structured_traces,
            "priority_rankings_summary": [
                {
                    "rank": item["priority_rank"],
                    "component": item["component"],
                    "udpi": item["udpi"],
                    "expected_gain": item["expected_reliability_gain"]
                }
                for item in rankings[:10]
            ]
        }

        # Save Report
        output_file = self.outputs_dir / "decision_report.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(report, f, indent=4)

        print("QUEST Decision Report Generated: outputs/decision_report.json")
        return report

    def handle_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handles decision-specific queries by invoking the appropriate decision module.
        """
        query_lower = query.lower()

        # 1. Simulating refactoring queries
        if "simulate" in query_lower:
            target = self.extract_target(query, context)
            if target and target != "repository":
                return {
                    "type": "SIMULATION",
                    "data": self.simulator.simulate_refactoring(target)
                }
            return {
                "error": "Please specify a valid component file path to simulate."
            }

        # 2. Dependency reasoning queries
        if "why" in query_lower or "trace" in query_lower or "dependency" in query_lower:
            target = self.extract_target(query, context)
            if target and target != "repository":
                return {
                    "type": "LINEAGE",
                    "data": self.reasoner.reason_dependencies(target)
                }

        # 3. Impact queries
        if "impact" in query_lower or "blast radius" in query_lower:
            target = self.extract_target(query, context)
            if target and target != "repository":
                return {
                    "type": "IMPACT",
                    "data": self.impact_analyzer.analyze_impact(target)
                }

        # 4. Default: Query priority rankings and recommendations
        return {
            "type": "DECISION_SUMMARY",
            "data": self.execute_decision_pipeline()
        }

    def extract_target(self, query: str, context: Dict[str, Any] = None) -> str:
        if context and context.get("component") and context.get("component") != "repository":
            return context["component"]
        
        # Fallback: search for words ending in .py
        for word in query.split():
            clean_word = word.strip(".,;:?!'\"")
            if clean_word.endswith(".py"):
                return clean_word
        return "repository"
