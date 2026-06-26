from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import time

# Import project quantum components.
from .quantum_encoder import QuantumEncoder
from .qsvm import QuantumRiskClassifier
from .quantum_walk import QuantumWalkEngine
from .qaoa import RiskQAOA
from .vqnn import VariationalQuantumNeuralNetwork



@dataclass
class QuantumExecutionResult:
    qaoa_result: Optional[Any] = None
    qsvm_result: Optional[Any] = None
    quantum_walk_result: Optional[Any] = None
    vqnn_result: Optional[Any] = None
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    successful_modules: Dict[str, bool] = field(default_factory=dict)


# Added production-ready pipeline request dataclass.
@dataclass
class QuantumPipelineRequest:
    repository: Any
    dependency_graph: Any
    repository_metrics: Dict[str, Any]
    module_names: Optional[Any] = None
    initial_risk: Optional[Dict[str, float]] = None
    training_features: Optional[Any] = None
    training_labels: Optional[Any] = None
    steps: Optional[int] = None


class QuantumPipeline:
    def __init__(
        self,
        encoder: Optional[QuantumEncoder] = None,
        qsvm: Optional[QuantumRiskClassifier] = None,
        quantum_walk: Optional[QuantumWalkEngine] = None,
        qaoa: Optional[RiskQAOA] = None,
        vqnn: Optional[VariationalQuantumNeuralNetwork] = None,
    ):
        self.encoder = encoder if encoder is not None else QuantumEncoder()
        self.qsvm = qsvm if qsvm is not None else QuantumRiskClassifier()
        self.quantum_walk = quantum_walk if quantum_walk is not None else QuantumWalkEngine()
        self.qaoa = qaoa if qaoa is not None else RiskQAOA()
        self.vqnn = vqnn if vqnn is not None else VariationalQuantumNeuralNetwork()
        self.last_result: Optional[QuantumExecutionResult] = None
        self.last_diagnostics: Dict[str, Any] = {}

    def execute_request(self, request: QuantumPipelineRequest) -> QuantumExecutionResult:
        """Execute the pipeline from a QuantumPipelineRequest."""
        if not isinstance(request, QuantumPipelineRequest):
            raise TypeError("request must be a QuantumPipelineRequest instance")
        return self.run(
            repository=request.repository,
            dependency_graph=request.dependency_graph,
            repository_metrics=request.repository_metrics,
            module_names=request.module_names,
            initial_risk=request.initial_risk,
            training_features=request.training_features,
            training_labels=request.training_labels,
            steps=request.steps,
        )

    def run(self, repository, dependency_graph, repository_metrics, **kwargs) -> QuantumExecutionResult:
        # Validate inputs
        pipeline_start = time.perf_counter()

        if repository is None:
            diagnostics_repository_missing = True
        else:
            diagnostics_repository_missing = False

        if dependency_graph is None:
            dependency_graph = {}

        if repository_metrics is None:
            repository_metrics = {}

        result = QuantumExecutionResult()
        diagnostics = {}
        successful_modules = {}
        diagnostics["pipeline"] = "running"

        # Encode repository features
        try:
            if hasattr(self.encoder, "encode_repository"):
                encoded_features = self.encoder.encode_repository(
                    repository_metrics
                )
            elif hasattr(self.encoder, "encode"):
                encoded_features = self.encoder.encode(
                    repository,
                    dependency_graph,
                    repository_metrics,
                )
            else:
                raise AttributeError(
                    "QuantumEncoder exposes neither 'encode_repository' nor 'encode'."
                )
            # Insert module_names extraction for QSVM if not provided
            if not kwargs.get("module_names") and isinstance(encoded_features, dict):
                kwargs["module_names"] = [
                    name for name in encoded_features.keys()
                    if not str(name).startswith("__")
                ]
            diagnostics["encoder"] = "success"
            diagnostics["encoded_feature_type"] = type(encoded_features).__name__
            diagnostics["encoded_feature_count"] = (
                len(encoded_features)
                if hasattr(encoded_features, "__len__")
                else 1
            )
            diagnostics["repository_missing"] = diagnostics_repository_missing
            diagnostics["repository_metric_count"] = len(repository_metrics)
            diagnostics["encoded_node_count"] = len(encoded_features) if hasattr(encoded_features, "__len__") else 0
            diagnostics["pipeline_validation"] = self.validate_pipeline()
        except Exception as e:
            diagnostics["encoder"] = f"failure: {str(e)}"
            diagnostics["pipeline"] = "completed"
            self.last_result = result
            self.last_diagnostics = dict(diagnostics)
            result.diagnostics = diagnostics
            return result

        # QSVM execution
        if self.qsvm is None:
            successful_modules["qsvm"] = False
            diagnostics["qsvm"] = "skipped: engine unavailable"
        else:
            diagnostics["qsvm_started"] = True
            module_start = time.perf_counter()
            try:
                result.qsvm_result = self._run_qsvm(encoded_features, **kwargs)
                diagnostics["qsvm_result_type"] = type(result.qsvm_result).__name__
                if isinstance(result.qsvm_result, dict):
                    diagnostics["qsvm_result_size"] = len(result.qsvm_result)
                    diagnostics["qsvm_sample_keys"] = list(result.qsvm_result.keys())[:5]
                diagnostics["qsvm"] = "success"
                diagnostics["qsvm_completed"] = True
                successful_modules["qsvm"] = True
            except Exception as e:
                diagnostics["qsvm"] = f"failure: {str(e)}"
                diagnostics["qsvm_exception"] = str(e)
                result.qsvm_result = None
                successful_modules["qsvm"] = False
            diagnostics["qsvm_execution_time"] = time.perf_counter() - module_start

        # Quantum Walk execution
        if self.quantum_walk is None:
            successful_modules["quantum_walk"] = False
            diagnostics["quantum_walk"] = "skipped: engine unavailable"
        else:
            diagnostics["quantum_walk_started"] = True
            module_start = time.perf_counter()
            try:
                result.quantum_walk_result = self._run_quantum_walk(
                    encoded_features,
                    dependency_graph=dependency_graph,
                    repository_metrics=repository_metrics,
                    **kwargs,
                )
                diagnostics["quantum_walk"] = "success"
                diagnostics["quantum_walk_completed"] = True
                successful_modules["quantum_walk"] = True
            except Exception as e:
                diagnostics["quantum_walk"] = f"failure: {str(e)}"
                diagnostics["quantum_walk_exception"] = str(e)
                successful_modules["quantum_walk"] = False
            diagnostics["quantum_walk_execution_time"] = time.perf_counter() - module_start

        # QAOA execution
        if self.qaoa is None:
            successful_modules["qaoa"] = False
            diagnostics["qaoa"] = "skipped: engine unavailable"
        else:
            diagnostics["qaoa_started"] = True
            module_start = time.perf_counter()
            try:
                result.qaoa_result = self._run_qaoa(encoded_features, **kwargs)
                diagnostics["qaoa"] = "success"
                diagnostics["qaoa_completed"] = True
                successful_modules["qaoa"] = True
            except Exception as e:
                diagnostics["qaoa"] = f"failure: {str(e)}"
                diagnostics["qaoa_exception"] = str(e)
                successful_modules["qaoa"] = False
            diagnostics["qaoa_execution_time"] = time.perf_counter() - module_start

        # VQNN execution
        if self.vqnn is None:
            successful_modules["vqnn"] = False
            diagnostics["vqnn"] = "skipped: engine unavailable"
        else:
            diagnostics["vqnn_started"] = True
            module_start = time.perf_counter()
            try:
                result.vqnn_result = self._run_vqnn(encoded_features, **kwargs)
                diagnostics["vqnn"] = "success"
                diagnostics["vqnn_completed"] = True
                successful_modules["vqnn"] = True
            except Exception as e:
                diagnostics["vqnn"] = f"failure: {str(e)}"
                diagnostics["vqnn_exception"] = str(e)
                successful_modules["vqnn"] = False
            diagnostics["vqnn_execution_time"] = time.perf_counter() - module_start

        diagnostics["pipeline"] = "completed"
        diagnostics["successful_module_count"] = sum(successful_modules.values())
        diagnostics["failed_module_count"] = len(successful_modules) - diagnostics["successful_module_count"]
        diagnostics["pipeline_execution_time"] = time.perf_counter() - pipeline_start
        diagnostics["summary"] = {
            "executed": len(successful_modules),
            "successful": sum(successful_modules.values()),
            "failed": len(successful_modules) - sum(successful_modules.values()),
        }
        result.successful_modules = successful_modules
        self.last_result = result
        self.last_diagnostics = dict(diagnostics)
        result.diagnostics = diagnostics
        return result

    def execute(self, repository, dependency_graph, repository_metrics, **kwargs):
        """
        Primary public execution entry point for the quantum pipeline.
        """
        return self.run(repository, dependency_graph, repository_metrics, **kwargs)

    def execute_modules(self, repository, dependency_graph, repository_metrics, **kwargs):
        """
        Convenience API for callers that prefer dictionary results for per-module quantum outputs.
        """
        result = self.run(repository, dependency_graph, repository_metrics, **kwargs)
        return {
            "qaoa": result.qaoa_result,
            "qsvm": result.qsvm_result,
            "quantum_walk": result.quantum_walk_result,
            "vqnn": result.vqnn_result,
            "diagnostics": result.diagnostics,
        }

    def update_query_engine(self, query_engine, execution_result):
        """
        Synchronizes pipeline results into the shared query context.
        """
        if not isinstance(execution_result, QuantumExecutionResult):
            raise TypeError("execution_result must be a QuantumExecutionResult instance")
        if not hasattr(query_engine, "update_quantum_results"):
            raise AttributeError("query_engine must have an 'update_quantum_results' method or attribute")
        context = query_engine.update_quantum_results(
            qaoa_result=execution_result.qaoa_result,
            qsvm_result=execution_result.qsvm_result,
            quantum_walk_result=execution_result.quantum_walk_result,
            vqnn_result=execution_result.vqnn_result,
        )
        if isinstance(context, dict):
            context["quantum_pipeline"] = "QuantumPipeline"
            context["quantum_pipeline_ready"] = True
        return context

    def get_last_result(self):
        """Return the last pipeline execution result."""
        return self.last_result

    def get_diagnostics(self):
        """Return diagnostics from the most recent execution."""
        return dict(self.last_diagnostics)

    def reset(self):
        """Reset cached execution state."""
        self.last_result = None
        self.last_diagnostics = {}

    def health_check(self):
        """Report availability of pipeline components."""
        return {
            "encoder": (self.encoder is not None) and (hasattr(self.encoder, "encode_repository") or hasattr(self.encoder, "encode")),
            "qsvm": (self.qsvm is not None) and (hasattr(self.qsvm, "predict") or hasattr(self.qsvm, "classify_modules")),
            "quantum_walk": (self.quantum_walk is not None) and hasattr(self.quantum_walk, "propagate_risk"),
            "qaoa": (self.qaoa is not None) and (hasattr(self.qaoa, "optimize") or hasattr(self.qaoa, "run") or hasattr(self.qaoa, "solve")),
            "vqnn": (self.vqnn is not None) and (hasattr(self.vqnn, "predict") or hasattr(self.vqnn, "infer") or hasattr(self.vqnn, "run")),
        }

    def validate_pipeline(self):
        """Validate that all required pipeline components expose supported APIs."""
        report = self.health_check()
        report["ready"] = all(report.values())
        return report

    def is_ready(self) -> bool:
        """Return True if the pipeline passes validation."""
        return self.validate_pipeline()["ready"]

    def execute_module(self, module_name, *args, **kwargs):
        """Execute a single quantum module by name."""
        dispatch = {
            "qsvm": self._run_qsvm,
            "quantum_walk": self._run_quantum_walk,
            "qaoa": self._run_qaoa,
            "vqnn": self._run_vqnn,
        }
        if module_name not in dispatch:
            raise ValueError(f"Unknown quantum module: {module_name}")
        return dispatch[module_name](*args, **kwargs)

    def _run_qsvm(self, encoded_features, **kwargs):
        module_names = kwargs.get("module_names")
        training_features = kwargs.get("training_features")
        training_labels = kwargs.get("training_labels")

        # Filter out keys starting with "__" from encoded_features if it's a dict
        if isinstance(encoded_features, dict):
            filtered_features = {
                k: v for k, v in encoded_features.items()
                if not str(k).startswith("__")
            }
        else:
            filtered_features = encoded_features

        # If module_names is not provided or empty, derive from filtered_features keys
        if not module_names:
            if isinstance(filtered_features, dict):
                module_names = [k for k in filtered_features.keys()]
            else:
                module_names = None

        # Filter filtered_features to only include module_names if both are dict/list
        if isinstance(filtered_features, dict) and module_names:
            filtered_features = {
                name: filtered_features[name]
                for name in module_names
                if name in filtered_features
            }

        if training_features is not None and training_labels is not None and hasattr(self.qsvm, "fit"):
            self.qsvm.fit(training_features, training_labels)

        # Always prefer classify_modules if available
        if hasattr(self.qsvm, "classify_modules"):
            result = self.qsvm.classify_modules(module_names, filtered_features)
            if result is None:
                raise RuntimeError("QSVM classify_modules() returned None.")
            return result
        elif hasattr(self.qsvm, "predict"):
            result = self.qsvm.predict(filtered_features)
            if result is None:
                raise RuntimeError("QSVM predict() returned None.")
            return result
        else:
            raise RuntimeError("QuantumRiskClassifier exposes no supported inference API.")

    def _run_quantum_walk(self, encoded_features, **kwargs):
        dependency_graph = kwargs.get("dependency_graph")
        initial_risk = kwargs.get("initial_risk")
        repository_metrics = kwargs.get("repository_metrics")
        steps = kwargs.get("steps")

        if hasattr(self.quantum_walk, "propagate_risk"):
            if steps is not None:
                return self.quantum_walk.propagate_risk(
                    dependencies=dependency_graph,
                    initial_risk=initial_risk,
                    repository_metrics=repository_metrics,
                    steps=steps,
                )
            else:
                return self.quantum_walk.propagate_risk(
                    dependencies=dependency_graph,
                    initial_risk=initial_risk,
                    repository_metrics=repository_metrics,
                )
        else:
            raise RuntimeError("QuantumWalkEngine exposes no supported propagation API.")

    def _run_qaoa(self, encoded_features, **kwargs):
        features = encoded_features
        if isinstance(encoded_features, dict):
            features = {
                k: v for k, v in encoded_features.items()
                if not str(k).startswith("__")
            }
        if hasattr(self.qaoa, "optimize"):
            return self.qaoa.optimize(features)
        elif hasattr(self.qaoa, "run"):
            return self.qaoa.run(features)
        elif hasattr(self.qaoa, "solve"):
            return self.qaoa.solve(features)
        else:
            raise RuntimeError("RiskQAOA exposes no supported execution API.")

    def _run_vqnn(self, encoded_features, **kwargs):
        features = encoded_features
        if isinstance(encoded_features, dict):
            features = {
                k: v for k, v in encoded_features.items()
                if not str(k).startswith("__")
            }
        if hasattr(self.vqnn, "predict"):
            return self.vqnn.predict(features)
        elif hasattr(self.vqnn, "infer"):
            return self.vqnn.infer(features)
        elif hasattr(self.vqnn, "run"):
            return self.vqnn.run(features)
        else:
            raise RuntimeError("VariationalQuantumNeuralNetwork exposes no supported inference API.")