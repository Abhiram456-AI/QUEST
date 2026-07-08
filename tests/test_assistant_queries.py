import unittest
from quest.retrieval.quest_assistant import QUESTAssistant

class TestAssistantQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assistant = QUESTAssistant()

    def test_repo_specific_queries(self):
        print("\n=========================================")
        print("TESTING REPO-SPECIFIC QUERIES")
        print("=========================================")
        queries = [
            "Is quest/quantum/qvnn_predictor.py reliable?",
            "Trace quest/intelligence/ast_analyzer.py from analysis to final decision",
            "What did reviewer and security agents find about quest/retrieval/quest_assistant.py?"
        ]
        for q in queries:
            response = self.assistant.ask(q)
            print(f"\nQUERY: {q}\nRESPONSE:\n{response}")
            self.assertIsNotNone(response)

    def test_general_queries(self):
        print("\n=========================================")
        print("TESTING GENERAL / METHODOLOGY QUERIES")
        print("=========================================")
        queries = [
            "Explain the overall project architecture",
            "What methodology is used to evaluate software trust in QUEST?",
            "How does the traditional tools compare to the quantum model?"
        ]
        for q in queries:
            response = self.assistant.ask(q)
            print(f"\nQUERY: {q}\nRESPONSE:\n{response}")
            self.assertIsNotNone(response)

    def test_ambiguous_queries(self):
        print("\n=========================================")
        print("TESTING AMBIGUOUS QUERIES")
        print("=========================================")
        queries = [
            "Should I check the code or run the quantum model for finding security risks?",
            "How do different components relate to trust and verification decision flow?"
        ]
        for q in queries:
            response = self.assistant.ask(q)
            print(f"\nQUERY: {q}\nRESPONSE:\n{response}")
            self.assertIsNotNone(response)

if __name__ == "__main__":
    unittest.main()
