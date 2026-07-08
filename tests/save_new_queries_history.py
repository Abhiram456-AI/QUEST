import json
from quest.retrieval.quest_assistant import QUESTAssistant

def run_new_queries():
    print("Initializing QUESTAssistant for new query tests...")
    assistant = QUESTAssistant()
    
    queries = [
        # Phase 1: Repository Intelligence
        "Which methods and variables were extracted in quest/decision/priority_ranker.py during Phase 1?",
        
        # Phase 2: Trust Representation
        "Analyze the Phase 2 trust features and security metrics computed for quest/decision/recommendation_engine.py.",
        
        # Phase 3: Quantum Intelligence
        "Compare the Schrödinger continuous-time quantum walk propagation and QVNN reliability state for quest/decision/scenario_simulator.py.",
        
        # Phase 4: Autonomous Agent Verification
        "What did the verification reviewer and critic agents report on the security/reliability of quest/decision/impact_analyzer.py?",
        
        # Phase 5: Knowledge Retrieval
        "Summarize the architectural roles of the newly added Phase 6 decision modules in the quest/decision folder.",
        
        # Phase 6: Decision Intelligence - Remediation Summary
        "What is the priority ranking and UDPI contributor breakdown for quest/decision/priority_ranker.py?",
        
        # Phase 6: Decision Intelligence - Lineage
        "Compute the dependency lineage and test linkage paths of quest/decision/recommendation_engine.py.",
        
        # Phase 6: Decision Intelligence - Blast Radius
        "Analyze the blast radius, indirect dependents, and critical path length of quest/decision/decision_engine.py.",
        
        # Phase 6: Decision Intelligence - Simulation
        "Simulate refactoring quest/decision/priority_ranker.py to calculate projected trust and overall reliability gains."
    ]
    
    for idx, query in enumerate(queries, 1):
        print(f"Running Query {idx}/{len(queries)}: {query}")
        response = assistant.ask(query)
        print(f"Response:\n{response}\n" + "-"*60 + "\n")
        
    print("Saving updated chat history to outputs/chat_history.json...")
    assistant.save_chat("outputs/chat_history.json")
    
    # Delete the root chat_history.json if present
    import os
    if os.path.exists("chat_history.json"):
        os.remove("chat_history.json")
        print("Successfully deleted the root chat_history.json file.")
    else:
        print("Root chat_history.json file not found, no deletion needed.")
        
    print("Successfully saved new queries!")

if __name__ == "__main__":
    run_new_queries()
