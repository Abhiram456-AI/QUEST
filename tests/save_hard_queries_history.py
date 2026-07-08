import json
from quest.retrieval.quest_assistant import QUESTAssistant

def run_and_save():
    print("Initializing QUESTAssistant to run queries...")
    assistant = QUESTAssistant()
    
    queries = [
        "Explain the trust score and risk profile for repository_scanner.py",
        "Trace test_repository_scanner.py from Phase 1 to Phase 4 agents",
        "Show the cyclomatic complexity and ast results for ast_analyzer.py",
        "Detail the test cases and class definitions inside test_ast_analyzer.py",
        "Compare reviewer security risk analysis versus quantum walk propagation for repository_scanner.py",
        "Why did the critic agent contradict the quantum walk results when evaluating ast_analyzer.py?",
        "What is the difference between traditional static analysis and the hybrid quantum-inspired walk model in QUEST?",
        "Does the call graph density and average degree influence the QSVM accuracy or does QVNN rely on normalized trust vectors?"
    ]
    
    for idx, query in enumerate(queries, 1):
        print(f"Running Query {idx}/{len(queries)}: {query}")
        # This will internally append the query and response to assistant.chat_history
        response = assistant.ask(query)
        
    print("Saving chat history to outputs/chat_history.json...")
    assistant.save_chat("outputs/chat_history.json")
    print("Successfully saved!")

if __name__ == "__main__":
    run_and_save()
