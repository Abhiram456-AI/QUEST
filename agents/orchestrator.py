from agents.reviewer import ReviewerAgent
from agents.critic import CriticAgent
from agents.security import SecurityAgent
from agents.explainer import ExplainerAgent
from agents.verifier import VerifierAgent

from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor


class BaseAgent(ABC):
    """
    Common interface that every QTrustCode agent must implement.
    """

    @abstractmethod
    def analyze(self, *args, **kwargs):
        pass


class AgentOrchestrator:
    """
    Coordinates all QTrustCode agents.

    For now this only wires the agents together.
    LLM models and detailed prompts will be attached later.

    All agents are expected to implement the BaseAgent interface.
    """

    def __init__(self, query_engine):
        self.query_engine = query_engine

        self.reviewer = ReviewerAgent(query_engine)
        self.critic = CriticAgent(query_engine)
        self.security = SecurityAgent(query_engine)
        self.explainer = ExplainerAgent(query_engine)
        self.verifier = VerifierAgent(query_engine)

    def _build_context(self, query: str):
        """
        Collect repository intelligence once and share it with all agents.
        """
        return {
            "query": query,
            "repository_metrics": self.query_engine.repository_metrics,
            "dependency_graph": self.query_engine.graph,
            "function_graph": getattr(self.query_engine, "function_graph", None),
            "knowledge_graph": getattr(self.query_engine, "knowledge_graph", None),
        }

    def analyze(self, query: str):
        context = self._build_context(query)

        with ThreadPoolExecutor(max_workers=4) as executor:
            reviewer_future = executor.submit(
                self.reviewer.analyze,
                query,
                context,
            )
            critic_future = executor.submit(
                self.critic.analyze,
                query,
                context,
            )
            security_future = executor.submit(
                self.security.analyze,
                query,
                context,
            )
            explainer_future = executor.submit(
                self.explainer.analyze,
                query,
                context,
            )

            reviewer_result = reviewer_future.result()
            critic_result = critic_future.result()
            security_result = security_future.result()
            explainer_result = explainer_future.result()

        verifier_result = self.verifier.analyze(
            reviewer_result,
            critic_result,
            security_result,
            explainer_result,
            context,
        )

        return {
            "query": query,
            "reviewer": reviewer_result,
            "critic": critic_result,
            "security": security_result,
            "explainer": explainer_result,
            "verifier": verifier_result,
        }