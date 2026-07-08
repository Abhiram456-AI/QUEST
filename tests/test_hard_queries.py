import sys
from quest.retrieval.quest_assistant import QUESTAssistant

def run_hard_queries():
    print("======================================================================")
    print("STRESSING QUEST RETRIEVAL: EXECUTING CHALLENGING & AMBIGUOUS QUERIES")
    print("======================================================================\n")
    
    assistant = QUESTAssistant()
    
    queries = [
        # 1. Component Disambiguation: Querying implementation file without "test"
        {
            "description": "Implementation Disambiguation (should target quest/intelligence/repository_scanner.py)",
            "query": "Explain the trust score and risk profile for repository_scanner.py"
        },
        # 2. Component Disambiguation: Querying test file with "test" keyword
        {
            "description": "Test Disambiguation (should target tests/test_repository_scanner.py)",
            "query": "Trace test_repository_scanner.py from Phase 1 to Phase 4 agents"
        },
        # 3. Component Disambiguation: Querying ast_analyzer implementation
        {
            "description": "Implementation Disambiguation (should target quest/intelligence/ast_analyzer.py)",
            "query": "Show the cyclomatic complexity and ast results for ast_analyzer.py"
        },
        # 4. Component Disambiguation: Querying test_ast_analyzer test
        {
            "description": "Test Disambiguation (should target tests/test_ast_analyzer.py)",
            "query": "Detail the test cases and class definitions inside test_ast_analyzer.py"
        },
        # 5. Ambiguous & Complex Query
        {
            "description": "Ambiguous/Multi-intent (Compares agents, quantum walks, and metrics)",
            "query": "Compare reviewer security risk analysis versus quantum walk propagation for repository_scanner.py"
        },
        # 6. Deep Trace Query with Critic & Agent analysis
        {
            "description": "Deep Trace (Should resolve to ast_analyzer implementation and show distinct agents in Phase 4)",
            "query": "Why did the critic agent contradict the quantum walk results when evaluating ast_analyzer.py?"
        },
        # 7. Methodology Query
        {
            "description": "Methodology / Novelty Query",
            "query": "What is the difference between traditional static analysis and the hybrid quantum-inspired walk model in QUEST?"
        },
        # 8. Multi-Intent Query combining QVNN & QSVM details
        {
            "description": "Multi-Intent Query (Quantum algorithms)",
            "query": "Does the call graph density and average degree influence the QSVM accuracy or does QVNN rely on normalized trust vectors?"
        }
    ]
    
    for idx, q_info in enumerate(queries, 1):
        print(f"--- QUERY #{idx}: {q_info['description']} ---")
        print(f"User Query: \"{q_info['query']}\"")
        
        response = assistant.ask(q_info["query"])
        
        print("\nQUEST Response:")
        print(response)
        print("-" * 70 + "\n")

if __name__ == "__main__":
    run_hard_queries()
