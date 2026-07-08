import unittest
import sys
from quest.retrieval.quest_assistant import QUESTAssistant

class TestAssistantStress(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Instantiate assistant
        cls.assistant = QUESTAssistant()

    def test_empty_query(self):
        print("\n--- Testing Empty Query ---")
        response = self.assistant.ask("")
        print(f"Query: ''\nResponse:\n{response}")
        self.assertIsNotNone(response)

    def test_whitespace_query(self):
        print("\n--- Testing Whitespace Query ---")
        response = self.assistant.ask("    ")
        print(f"Query: '    '\nResponse:\n{response}")
        self.assertIsNotNone(response)

    def test_gibberish_query(self):
        print("\n--- Testing Gibberish Query ---")
        response = self.assistant.ask("qwxzytrskljhgfdapeoimbvcunh")
        print(f"Query: 'qwxzytrskljhgfdapeoimbvcunh'\nResponse:\n{response}")
        self.assertIsNotNone(response)

    def test_very_long_query(self):
        print("\n--- Testing Very Long Query ---")
        long_query = "quantum " * 1000  # 1000 words
        response = self.assistant.ask(long_query)
        print(f"Query Length: {len(long_query)} chars\nResponse snippet:\n{response[:200]}")
        self.assertIsNotNone(response)

    def test_injection_queries(self):
        print("\n--- Testing Code/SQL/HTML Injection Queries ---")
        queries = [
            "../../../etc/passwd",
            "<script>alert('xss')</script>",
            "SELECT * FROM users WHERE username = 'admin' OR '1'='1'",
            "file:../main.py; rm -rf /"
        ]
        for q in queries:
            response = self.assistant.ask(q)
            print(f"Query: {q}\nResponse:\n{response}")
            self.assertIsNotNone(response)

    def test_ambiguous_multi_intent_query(self):
        print("\n--- Testing Ambiguous/Multi-Intent Query ---")
        # Combines quantum, walk, optimization, review, verifier, architecture, and differences.
        query = "Compare quantum walks vs. reviewer verifier architecture differences for QAOA optimization"
        response = self.assistant.ask(query)
        print(f"Query: {query}\nResponse:\n{response}")
        self.assertIsNotNone(response)

if __name__ == "__main__":
    unittest.main()
