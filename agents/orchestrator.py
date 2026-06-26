from agents.reviewer import ReviewerAgent
from agents.critic import CriticAgent
from agents.security import SecurityAgent
from agents.explainer import ExplainerAgent
from agents.verifier import VerifierAgent

# Quantum-aware imports
from quantum.quantum_context import QuantumContext
from quantum.quantum_builder import QuantumContextBuilder
from quantum.quantum_pipeline import (
    QuantumPipeline,
    QuantumPipelineRequest,
)

from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
import os
import time
from typing import Dict, Any


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

    MAX_WORKERS = 4
    VERSION = "quantum_v1"

    def __init__(self, query_engine):
        self.query_engine = query_engine

        self.quantum_builder = QuantumContextBuilder()
        self.quantum_context = QuantumContext()
        self.quantum_pipeline = QuantumPipeline()
        self.max_workers = min(
            self.MAX_WORKERS,
            max(1, os.cpu_count() or 1),
        )

        self.reviewer = ReviewerAgent(
            query_engine,
            self.quantum_context,
        )
        self.critic = CriticAgent(
            query_engine,
            self.quantum_context,
        )
        self.security = SecurityAgent(
            query_engine,
            self.quantum_context,
        )
        self.explainer = ExplainerAgent(
            query_engine,
            self.quantum_context,
        )
        self.verifier = VerifierAgent(
            query_engine,
            self.quantum_context,
        )

    def _sync_quantum_context(self):
        """Synchronize the latest QuantumContext instance with all agents."""
        for agent in (
            self.reviewer,
            self.critic,
            self.security,
            self.explainer,
            self.verifier,
        ):
            if hasattr(agent, "quantum_context"):
                agent.quantum_context = self.quantum_context

    def _execute_quantum_pipeline(self, context: Dict[str, Any]):
        """Execute the quantum pipeline and synchronize results into the query engine."""
        try:
            if not self.quantum_pipeline.is_ready():
                context.setdefault("quantum_pipeline", {})
                context["quantum_pipeline"]["status"] = "not_ready"
                return

            request = QuantumPipelineRequest(
                repository=getattr(self.query_engine, "repository", None),
                dependency_graph=context.get("dependency_graph"),
                repository_metrics=context.get("repository_metrics") or {},
                module_names=context.get("repository_nodes"),
                initial_risk=context.get("initial_risk"),
            )

            execution = self.quantum_pipeline.execute_request(request)
            context["quantum_pipeline_result"] = execution

            updated_context = self.quantum_pipeline.update_query_engine(
                self.query_engine,
                execution,
            )
            if isinstance(updated_context, dict):
                context.update(updated_context)

            context.update(
                {
                    "qaoa_result": execution.qaoa_result,
                    "qsvm_result": execution.qsvm_result,
                    "quantum_walk_result": execution.quantum_walk_result,
                    "vqnn_result": execution.vqnn_result,
                    "quantum_pipeline": {
                        "status": "executed",
                        "diagnostics": execution.diagnostics,
                        "successful_modules": execution.successful_modules,
                    },
                }
            )
        except Exception as exc:
            context.setdefault("quantum_pipeline", {})
            context["quantum_pipeline"]["status"] = "failed"
            context["quantum_pipeline"]["error"] = str(exc)

    def _build_quantum_context(
        self,
        context: Dict[str, Any],
    ):
        try:
            # Use tuple for quantum result names
            quantum_result_names = (
                "qaoa_result",
                "qsvm_result",
                "quantum_walk_result",
                "vqnn_result",
            )
            # Synchronize quantum results from query_engine if missing in context
            for name in quantum_result_names:
                if context.get(name) is None and getattr(self.query_engine, name, None) is not None:
                    context[name] = getattr(self.query_engine, name)

            repository_nodes = list(
                context.get(
                    "repository_nodes",
                    getattr(
                        self.query_engine,
                        "repository_nodes",
                        [],
                    ),
                )
                or []
            )
            # Debug (optional)
            print(f"Repository Nodes: {len(repository_nodes)}")
            print(
                "Quantum inputs:",
                {
                    "qaoa": context.get("qaoa_result") is not None,
                    "qsvm": context.get("qsvm_result") is not None,
                    "walk": context.get("quantum_walk_result") is not None,
                    "vqnn": context.get("vqnn_result") is not None,
                },
            )
            self.quantum_context = (
                self.quantum_builder.build(
                    repository_nodes=repository_nodes,
                    qaoa_result=context.get(
                        "qaoa_result"
                    ),
                    qsvm_result=context.get(
                        "qsvm_result"
                    ),
                    quantum_walk_result=context.get(
                        "quantum_walk_result"
                    ),
                    vqnn_result=context.get(
                        "vqnn_result"
                    ),
                    metadata={
                        "repository_metrics": context.get(
                            "repository_metrics",
                            {},
                        ),
                        "dependency_graph": context.get(
                            "dependency_graph"
                        ),
                        "function_graph": context.get(
                            "function_graph"
                        ),
                        "knowledge_graph": context.get(
                            "knowledge_graph"
                        ),
                    },
                )
            )
            # After building, populate context quantum results from quantum_context if missing
            for name in quantum_result_names:
                if context.get(name) is None and hasattr(self.quantum_context, name):
                    context[name] = getattr(self.quantum_context, name)

            # Debug (optional)
            print(f"Quantum Nodes: {len(self.quantum_context.nodes)}")

            context["quantum_context"] = (
                self.quantum_context.to_dict()
                if hasattr(
                    self.quantum_context,
                    "to_dict",
                )
                else self.quantum_context
            )
            context["quantum_enabled"] = self.quantum_context is not None
            context["quantum_error"] = None

            self._sync_quantum_context()
            context["quantum_pipeline_status"] = context.get(
                "quantum_pipeline", {}
            ).get("status")

        except Exception as exc:
            context["quantum_context"] = (
                self.quantum_context.to_dict()
                if hasattr(
                    self.quantum_context,
                    "to_dict",
                )
                else self.quantum_context
            )
            context["quantum_enabled"] = False
            context["quantum_error"] = str(exc)
            context["quantum_pipeline_status"] = "builder_failed"

    def _safe_result(
        self,
        future,
        agent_name,
    ):
        try:
            return future.result()
        except Exception as exc:
            return {
                "agent": agent_name,
                "status": "ERROR",
                "confidence": 0.0,
                "error": str(exc),
                "assessment_performed": False,
                "status_message": (
                    f"{agent_name} agent execution failed"
                ),
            }

    @staticmethod
    def _metadata(
        max_workers,
        quantum_enabled,
    ):
        return {
            "version": AgentOrchestrator.VERSION,
            "max_workers": max_workers,
            "quantum_enabled": quantum_enabled,
        }

    def _query_engine_context(self) -> Dict[str, Any]:
        if hasattr(
            self.query_engine,
            "get_context",
        ):
            try:
                context = (
                    self.query_engine.get_context()
                )
                if not isinstance(context, dict):
                    context = {}
                if isinstance(context, dict):
                    return context
            except Exception:
                pass
        return {}

    def _build_context(self, query: str) -> Dict[str, Any]:
        """
        Collect repository intelligence once and share it with all agents.
        """
        qe_context = (
            self._query_engine_context()
        )

        if not isinstance(qe_context, dict):
            qe_context = {}

        return {
            "query": query,
            "repository_metrics": qe_context.get(
                "repository_metrics",
                getattr(
                    self.query_engine,
                    "repository_metrics",
                    {},
                ),
            ),
            "dependency_graph": qe_context.get(
                "dependency_graph",
                getattr(
                    self.query_engine,
                    "graph",
                    None,
                ),
            ),
            "function_graph": qe_context.get(
                "function_graph",
                getattr(
                    self.query_engine,
                    "function_graph",
                    None,
                ),
            ),
            "knowledge_graph": qe_context.get(
                "knowledge_graph",
                getattr(
                    self.query_engine,
                    "knowledge_graph",
                    None,
                ),
            ),
            "qaoa_result": qe_context.get(
                "qaoa_result"
            ),
            "qsvm_result": qe_context.get(
                "qsvm_result"
            ),
            "quantum_walk_result": qe_context.get(
                "quantum_walk_result"
            ),
            "vqnn_result": qe_context.get(
                "vqnn_result"
            ),
            "repository_nodes": qe_context.get(
                "repository_nodes",
                list(
                    getattr(
                        self.query_engine,
                        "repository_nodes",
                        [],
                    )
                ),
            ),
            "quantum_context": (
                self.quantum_context.to_dict()
                if hasattr(
                    self.quantum_context,
                    "to_dict",
                )
                else self.quantum_context
            ),
            "quantum_enabled": True,
            "quantum_error": None,
        }

    def analyze(self, query: str):
        context = self._build_context(query)
        context.setdefault("qaoa_result", None)
        context.setdefault("qsvm_result", None)
        context.setdefault("quantum_walk_result", None)
        context.setdefault("vqnn_result", None)
        self._execute_quantum_pipeline(context)
        if context.get("quantum_pipeline", {}).get("status") == "failed":
            print("Quantum pipeline failed:", context["quantum_pipeline"].get("error"))
        start_time = time.perf_counter()

        self._build_quantum_context(
            context
        )

        with ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
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

            reviewer_result = self._safe_result(
                reviewer_future,
                "reviewer",
            )
            critic_result = self._safe_result(
                critic_future,
                "critic",
            )
            security_result = self._safe_result(
                security_future,
                "security",
            )
            explainer_result = self._safe_result(
                explainer_future,
                "explainer",
            )

        agent_execution_seconds = round(
            max(
                0.0,
                time.perf_counter() - start_time,
            ),
            4,
        )

        try:
            verifier_result = self.verifier.analyze(
                reviewer_result,
                critic_result,
                security_result,
                explainer_result,
                context,
            )
        except Exception as exc:
            verifier_result = {
                "status": "ERROR",
                "confidence": 0.0,
                "error": str(exc),
                "assessment_performed": False,
                "status_message": (
                    "Verifier execution failed"
                ),
            }

        total_execution_seconds = round(
            max(
                0.0,
                time.perf_counter() - start_time,
            ),
            4,
        )

        pipeline_status = (
            "SUCCESS"
            if verifier_result.get(
                "status"
            ) != "ERROR"
            else "PARTIAL_FAILURE"
        )

        return {
            "query": query,
            "reviewer": reviewer_result,
            "critic": critic_result,
            "security": security_result,
            "explainer": explainer_result,
            "verifier": verifier_result,
            "quantum_enabled": context[
                "quantum_enabled"
            ],
            "quantum_context": (
                self.quantum_context.to_dict()
                if hasattr(
                    self.quantum_context,
                    "to_dict",
                )
                else self.quantum_context
            ),
            "context": {
                **context,
                "quantum_context": (
                    self.quantum_context.to_dict()
                    if hasattr(
                        self.quantum_context,
                        "to_dict",
                    )
                    else context.get(
                        "quantum_context"
                    )
                ),
            },
            "quantum_error": context[
                "quantum_error"
            ],
            "framework": "QTrustCode",
            "framework_version": self.VERSION,
            "orchestrator_metadata": (
                self._metadata(
                    self.max_workers,
                    context[
                        "quantum_enabled"
                    ],
                )
            ),
            "pipeline_status": (
                pipeline_status
            ),
            "performance": {
                "agent_execution_seconds": (
                    agent_execution_seconds
                ),
                "total_execution_seconds": (
                    total_execution_seconds
                ),
            },
        }