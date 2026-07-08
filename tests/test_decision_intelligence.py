import unittest
import json
from pathlib import Path
from quest.decision.priority_ranker import PriorityRanker
from quest.decision.impact_analyzer import ImpactAnalyzer
from quest.decision.dependency_reasoner import DependencyReasoner
from quest.decision.recommendation_engine import RecommendationEngine
from quest.decision.scenario_simulator import ScenarioSimulator
from quest.decision.decision_engine import DecisionEngine
from quest.retrieval.quest_assistant import QUESTAssistant

class TestDecisionIntelligence(unittest.TestCase):
    """
    Test suite for Phase 6 Decision Intelligence.
    """

    def setUp(self):
        self.outputs_dir = Path("outputs")

    def test_priority_ranker(self):
        ranker = PriorityRanker(self.outputs_dir)
        rankings = ranker.calculate_priority_rankings()
        self.assertIsInstance(rankings, list)
        self.assertTrue(len(rankings) > 0)
        
        # Verify keys are present
        first = rankings[0]
        self.assertIn("component", first)
        self.assertIn("udpi", first)
        self.assertIn("expected_reliability_gain", first)
        self.assertIn("priority_rank", first)
        self.assertEqual(first["priority_rank"], 1)

    def test_impact_analyzer(self):
        analyzer = ImpactAnalyzer(self.outputs_dir)
        # 1. Test full run
        full_impacts = analyzer.analyze_impact()
        self.assertIsInstance(full_impacts, dict)
        self.assertTrue(len(full_impacts) > 0)

        # 2. Test single file impact
        single = analyzer.analyze_impact("main.py")
        self.assertIn("direct_dependents", single)
        self.assertIn("transitive_dependents", single)
        self.assertIn("impact_rating", single)
        self.assertIn("impact_score", single)

    def test_dependency_reasoner(self):
        reasoner = DependencyReasoner(self.outputs_dir)
        reasoning = reasoner.reason_dependencies("quest/retrieval/quest_assistant.py")
        self.assertIsInstance(reasoning, dict)
        self.assertIn("lineage_explanation", reasoning)
        self.assertIn("shortest_path_from_main", reasoning)
        self.assertIn("direct_incoming_imports", reasoning)

    def test_recommendation_engine(self):
        engine = RecommendationEngine(self.outputs_dir)
        recommendations = engine.generate_recommendations(limit=3)
        self.assertIsInstance(recommendations, list)
        self.assertTrue(len(recommendations) > 0)
        
        first = recommendations[0]
        self.assertIn("component", first)
        self.assertIn("remediations", first)
        self.assertTrue(len(first["remediations"]) > 0)

    def test_scenario_simulator(self):
        simulator = ScenarioSimulator(self.outputs_dir)
        result = simulator.simulate_refactoring("quest/retrieval/quest_assistant.py")
        self.assertIsInstance(result, dict)
        self.assertIn("simulated_component", result)
        self.assertIn("baseline_observed", result)
        self.assertIn("simulated_counterfactual", result)
        self.assertIn("repository_impact", result)
        
        impact = result["repository_impact"]
        self.assertIn("percentage_improvement", impact)
        self.assertTrue(impact["percentage_improvement"] >= 0.0)

    def test_decision_assistant_queries(self):
        assistant = QUESTAssistant()
        
        # Test remediation summary
        r1 = assistant.ask("Which three files should I fix first?")
        self.assertIn("QUEST Analysis Type: DECISION_QUERY", r1)
        self.assertIn("=== QUEST Health Overview ===", r1)
        self.assertIn("=== Top Remediation Action Plans ===", r1)

        # Test impact query
        r2 = assistant.ask("What is the blast radius and impact of main.py?")
        self.assertIn("QUEST Analysis Type: DECISION_QUERY (Blast Radius Impact)", r2)
        self.assertIn("=== QUEST Impact Blast Radius ===", r2)

        # Test lineage query
        r3 = assistant.ask("What is the dependency lineage of quest/retrieval/quest_assistant.py?")
        self.assertIn("QUEST Analysis Type: DECISION_QUERY (Lineage Explanation)", r3)
        self.assertIn("=== QUEST Lineage Trace ===", r3)

        # Test simulation query
        r4 = assistant.ask("Simulate refactoring quest/retrieval/quest_assistant.py")
        self.assertIn("QUEST Analysis Type: DECISION_QUERY (Simulation)", r4)
        self.assertIn("=== QUEST Counterfactual Scenario Engine ===", r4)

    def test_final_decision_resolver(self):
        from quest.decision.final_decision_resolver import FinalDecisionResolver
        resolver = FinalDecisionResolver(self.outputs_dir)
        context = {
            "component": "quest/decision/decision_engine.py",
            "evidence_count": 4,
            "intent": "DECISION_QUERY",
            "reasoning_chain": {
                "quantum_analysis": [
                    {
                        "component": "quest/decision/decision_engine.py",
                        "content": {
                            "propagation_risk": 0.85,
                            "reliability_score": 0.90
                        }
                    }
                ],
                "agent_analysis": [
                    {
                        "component": "quest/decision/decision_engine.py",
                        "content": {
                            "severity": "HIGH",
                            "agent_name": "reviewer"
                        }
                    },
                    {
                        "component": "quest/decision/decision_engine.py",
                        "content": {
                            "severity": "LOW",
                            "agent_name": "critic"
                        }
                    },
                    {
                        "component": "quest/decision/decision_engine.py",
                        "content": {
                            "severity": "MEDIUM",
                            "agent_name": "security"
                        }
                    }
                ]
            }
        }
        res = resolver.resolve(context, "Initial low priority warning.")
        
        # Assert confidence capped and disagreement penalty applied
        self.assertTrue(res["resolved_confidence"] <= 0.30)
        self.assertEqual(res["resolved_risk"], "REVIEW_REQUIRED")
        
        # Check metrics mapping
        metrics = res["metrics"]
        self.assertIn("evidence_confidence", metrics)
        self.assertIn("decision_confidence", metrics)
        self.assertIn("prediction_confidence", metrics)

    def test_sensitivity_analysis(self):
        ranker = PriorityRanker(self.outputs_dir)
        rankings = ranker.calculate_priority_rankings()
        
        # Verify sensitivity report is generated
        report_path = self.outputs_dir / "weights_sensitivity_report.json"
        self.assertTrue(report_path.exists())
        
        with open(report_path, "r") as f:
            report = json.load(f)
        
        # Check sensitivity metrics
        for key in ["trust", "quantum_walk", "qaoa", "qvnn", "agents", "dependency_centrality", "complexity"]:
            self.assertIn(key, report)
            self.assertIn("kendall_tau_perturbation", report[key])
            self.assertIn("robustness", report[key])
            self.assertTrue(-1.0 <= report[key]["kendall_tau_perturbation"] <= 1.0)

    def test_simulation_statistics(self):
        simulator = ScenarioSimulator(self.outputs_dir)
        result = simulator.simulate_refactoring("quest/retrieval/quest_assistant.py")
        
        impact = result.get("repository_impact", {})
        self.assertIn("standard_error_mean", impact)
        self.assertIn("confidence_interval_95", impact)
        self.assertIn("normality_check", impact)
        
        ci = impact["confidence_interval_95"]
        self.assertEqual(len(ci), 2)
        self.assertTrue(ci[0] <= ci[1])
        
        norm = impact["normality_check"]
        self.assertIn("skewness", norm)
        self.assertIn("kurtosis", norm)
        self.assertIn("is_normal", norm)

if __name__ == "__main__":
    unittest.main()
