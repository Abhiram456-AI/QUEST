"""
QUEST: Quantum Evaluation of Software Trust

Phase 5:
Context Retrieval & Query Intelligence Engine

Module:
Context Builder

Purpose:
Transforms retrieved evidence chunks into structured reasoning context.

Converts:
Retrieved Evidence
        ↓
Organized QUEST Reasoning Context
        ↓
Assistant-ready Knowledge
"""


from pathlib import Path
from typing import Dict, List

from quest.retrieval.retrieval_engine import RetrievalEngine


class ContextBuilder:
    """
    Builds structured reasoning context from retrieved QUEST evidence.
    """

    def __init__(self):

        self.retriever = RetrievalEngine()


    def build_context(
        self,
        query: str
    ) -> Dict:
        """
        Creates structured context for a user query.
        """
        evidence = self.retriever.retrieve(
            query=query,
            top_k=15  # Fetch more initially to allow robust filtering
        )

        # Route query to find intent
        from quest.retrieval.query_router import QueryRouter
        router = QueryRouter()
        intent = router.route(query).intent

        # Deduplicate evidence by (source, component, content) signature
        import json
        seen_evidence = set()
        unique_evidence = []
        for item in evidence:
            source = item.get("source", "")
            component = item.get("component", "")
            content = item.get("content", "")
            
            if isinstance(content, (dict, list)):
                content_str = json.dumps(content, sort_keys=True)
            else:
                content_str = str(content)
            try:
                parsed = json.loads(content_str)
                content_str = json.dumps(parsed, sort_keys=True)
            except Exception:
                pass
            
            sig = (source, component, content_str)
            if sig not in seen_evidence:
                seen_evidence.add(sig)
                unique_evidence.append(item)

        # Detect the target component from query and unique evidence candidates
        target_component = self.detect_component(unique_evidence, query)

        # Filter evidence chunks dynamically by component and intent
        filtered_evidence = []
        for item in unique_evidence:
            comp = item.get("component", "")
            cat = item.get("category", "")
            
            # Component matching: if we are querying a specific component, exclude other specific components
            if target_component != "repository" and comp != "repository" and comp != target_component:
                continue
                
            # Intent/Category matching:
            if intent in ["ARCHITECTURE_QUERY", "DEPENDENCY_QUERY", "AST_QUERY", "CODE_QUERY", "METRIC_QUERY"]:
                # Exclude risk/quantum/agent files for structural questions
                if cat in ["quantum", "agent"]:
                    continue
            elif intent in ["RISK_QUERY", "AGENT_QUERY"]:
                # Prioritize agent/quantum, but don't strictly exclude
                pass
                
            filtered_evidence.append(item)

        # Limit to top 8 filtered evidence items to prevent context overflow
        filtered_evidence = filtered_evidence[:8]

        context = {
            "query": query,
            "evidence_count": len(filtered_evidence),
            "component": target_component,
            "reasoning_chain": {
                "repository_analysis": [],
                "trust_analysis": [],
                "quantum_analysis": [],
                "agent_analysis": []
            },
            "raw_evidence": []
        }

        for item in filtered_evidence:
            formatted = self.format_evidence(item)
            context["raw_evidence"].append(formatted)

            category = item.get("category", "unknown")
            if category == "repository":
                context["reasoning_chain"]["repository_analysis"].append(formatted)
            elif category == "trust":
                context["reasoning_chain"]["trust_analysis"].append(formatted)
            elif category == "quantum":
                context["reasoning_chain"]["quantum_analysis"].append(formatted)
            elif category == "agent":
                context["reasoning_chain"]["agent_analysis"].append(formatted)

        # Apply secondary content-aware deduplication to reasoning_chain categories
        import json
        for cat in context["reasoning_chain"]:
            seen_cat = []
            deduped_cat = []
            for item in context["reasoning_chain"][cat]:
                content_dict = item.get("content", {})
                if isinstance(content_dict, str):
                    try:
                        content_dict = json.loads(content_dict)
                    except Exception:
                        pass
                
                if cat == "agent_analysis" and isinstance(content_dict, dict):
                    sig = (item.get("component"), content_dict.get("agent_name"), content_dict.get("finding"))
                else:
                    sig = (item.get("component"), json.dumps(content_dict, sort_keys=True))
                
                if sig not in seen_cat:
                    seen_cat.append(sig)
                    deduped_cat.append(item)
            context["reasoning_chain"][cat] = deduped_cat

        context["evidence_count"] = sum(len(layer) for layer in context["reasoning_chain"].values())
        return context


    def format_evidence(
        self,
        evidence: Dict
    ) -> Dict:
        """
        Normalizes evidence format for reasoning.
        """

        return {
            "id": evidence.get(
                "evidence_id"
            ),

            "component": evidence.get(
                "component"
            ),

            "source": evidence.get(
                "source"
            ),

            "category": evidence.get(
                "category"
            ),

            "phase": evidence.get(
                "metadata",
                {}
            ).get(
                "phase"
            ),

            "importance": evidence.get(
                "metadata",
                {}
            ).get(
                "importance"
            ),

            "content": evidence.get(
                "content"
            )
        }


    def detect_component(
        self,
        evidence: List[Dict],
        query: str = ""
    ):
        """
        Finds the primary component being reasoned about, disambiguating
        between test files and actual implementation files.
        """
        # Load all file paths from repository intelligence
        repo_intel_path = Path("outputs/repository_intelligence.json")
        all_paths = []
        if repo_intel_path.exists():
            try:
                import json
                with open(repo_intel_path, "r") as f:
                    intel = json.load(f)
                    all_paths = [item.get("file") for item in intel.get("files", []) if item.get("file")]
            except Exception:
                pass

        # Extract potential filename mentions from the query
        query_lower = query.lower()
        query_terms = [t.lower() for t in query.split()]
        
        # Check if the query specifically mentions any files in the repository
        best_exact = None
        exact_rank = -9999
        for p in all_paths:
            p_lower = p.lower()
            p_filename = p_lower.split("/")[-1]
            if p_filename in query_lower:
                # Prioritize exact filename matches, preferring non-test files
                is_test = "test_" in p_lower or "/tests/" in p_lower
                rank = 10 if not is_test else -10
                if rank > exact_rank:
                    exact_rank = rank
                    best_exact = p
        
        if best_exact:
            return best_exact

        # Fallback to evidence candidate scoring if no exact filename matches are found in query
        query_has_test = any("test" in t for t in query_terms)
        has_mention = False
        candidates = []
        for item in evidence:
            component = item.get("component")
            if component and component != "repository":
                candidates.append(component)
                
                base_name = Path(component).stem.lower()
                if base_name in query.lower() or component.lower() in query.lower():
                    has_mention = True

        if not has_mention or not candidates:
            return "repository"

        best_candidate = None
        best_score = -9999

        for candidate in candidates:
            score = 0
            candidate_lower = candidate.lower()
            cand_is_test = "test" in candidate_lower or "tests/" in candidate_lower

            if cand_is_test:
                if query_has_test:
                    score += 10
                else:
                    score -= 10
            else:
                if not query_has_test:
                    score += 10

            for term in query_terms:
                clean_term = term.replace(".py", "")
                if clean_term in candidate_lower:
                    score += 5

            if score > best_score:
                best_score = score
                best_candidate = candidate

        return best_candidate if best_candidate else candidates[0]




if __name__ == "__main__":

    builder = ContextBuilder()

    context = builder.build_context(
        "Why is repository_scanner.py risky"
    )

    print("QUEST Context Generated")

    print(
        "Component:",
        context["component"]
    )

    for stage, evidence in context[
        "reasoning_chain"
    ].items():

        print(
            stage,
            len(evidence)
        )