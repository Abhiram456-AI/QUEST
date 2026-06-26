import json
from pprint import pprint
import time
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from datetime import datetime

from parser.repository_parser import (
    RepositoryParser,
)
from context.graph_builder import (
    DependencyGraphBuilder,
)
from features.repository_metrics import (
    RepositoryMetrics,
)
from context.function_graph_builder import (
    FunctionGraphBuilder,
)
from context.knowledge_graph_builder import (
    KnowledgeGraphBuilder,
)

from reasoning.query_engine import (
    QueryEngine,
)
from reasoning.path_engine import (
    PathEngine,
)
from reasoning.impact_engine import (
    ImpactEngine,
)
from reasoning.coupling_engine import (
    CouplingEngine,
)
from reasoning.risk_engine import (
    RiskEngine,
)
from reasoning.execution_engine import (
    ExecutionEngine,
)
from agents.orchestrator import (
    AgentOrchestrator,
)


if __name__ == "__main__":
    repository_path = input("Repository Path: ")
    repository_path = repository_path.strip()

    if not repository_path:
        raise ValueError(
            "Repository path cannot be empty."
        )

    repository_path = str(
        Path(repository_path).expanduser()
    )
    if not Path(repository_path).exists():
        raise FileNotFoundError(
            f"Repository does not exist: {repository_path}"
        )

    parser = RepositoryParser(repository_path)

    print("\nParsing repository...\n")
    repository = parser.parse()
    print(
        f"Parsed {len(repository.files)} files."
    )
    if not repository.files:
        raise ValueError(
            "No parsable source files were found in the repository."
        )

    builder = DependencyGraphBuilder()
    graph = builder.build(repository)
    print(
        f"Dependency Nodes: {graph.number_of_nodes()}"
    )
    print(
        f"Dependency Edges: {graph.number_of_edges()}"
    )

    print("\nDEPENDENCY EDGES:\n")

    for source, target in graph.edges():
        print(f"{source} ---> {target}")

    result = {path: asdict(metadata) for path, metadata in repository.files.items()}

    print(json.dumps(result, indent=4))

    metrics_engine = RepositoryMetrics(graph, repository)

    metrics = metrics_engine.compute()

    print("\nREPOSITORY METRICS\n")

    for file, values in metrics.items():
        print(file)
        print(values)
        print()

    function_builder = FunctionGraphBuilder()

    function_graph = function_builder.build(repository)

    print("\nFUNCTION CALL EDGES:\n")
    print(f"Function Nodes: {function_graph.number_of_nodes()}")

    print(f"Function Edges: {function_graph.number_of_edges()}\n")

    for source, target in function_graph.edges():
        print(f"{source} ---> {target}")

    dependency_path_engine = PathEngine(graph)

    function_path_engine = PathEngine(function_graph)
    execution_engine = ExecutionEngine(function_graph)

    impact_engine = ImpactEngine(graph)
    coupling_engine = CouplingEngine(graph)
    risk_engine = RiskEngine(
        metrics=metrics,
        impact_engine=impact_engine,
        coupling_engine=coupling_engine,
    )

    knowledge_builder = KnowledgeGraphBuilder()

    knowledge_graph = knowledge_builder.build(repository)

    knowledge_path_engine = PathEngine(knowledge_graph)

    print("\nKNOWLEDGE GRAPH:\n")

    print(f"Knowledge Nodes: " f"{knowledge_graph.number_of_nodes()}")

    print(f"Knowledge Edges: " f"{knowledge_graph.number_of_edges()}")

    relations = defaultdict(list)

    for source, target, data in knowledge_graph.edges(data=True):
        relations[data["relation"]].append((source, target))

    for relation, edges in relations.items():
        print(f"\n{relation} EDGES:")
        print("-" * 50)

        for source, target in edges:
            print(f"{source} ---> {target}")

    query_engine = QueryEngine(
        repository=repository,
        dependency_graph=graph,
        function_graph=function_graph,
        knowledge_graph=knowledge_graph,
        metrics=metrics,
        dependency_path_engine=dependency_path_engine,
        function_path_engine=function_path_engine,
        knowledge_path_engine=knowledge_path_engine,
        impact_engine=impact_engine,
        coupling_engine=coupling_engine,
        risk_engine=risk_engine,
        execution_engine=execution_engine,
    )
    orchestrator = AgentOrchestrator(query_engine)

    print("\nQTRUSTCODE QUANTUM FRAMEWORK READY")
    print(f"Framework: QTrustCode")
    print(f"Version: {orchestrator.VERSION}")
    print(
        f"Workers: {orchestrator.max_workers}"
    )

    print("\nQUERY ENGINE READY")
    print("Type 'exit' to quit.\n")
    last_result = None
    session_queries = 0

    while True:
        query = input("QTrustCode > ").strip()

        if query.lower() == "help":
            print(
                "\nExamples:"
                "\n- show risk of main.py"
                "\n- explain authentication.py"
                "\n- show dependencies of orchestrator.py"
                "\n- show impact of parser.py"
                "\n- show execution flow of main.py"
                "\n- explain security risks of authentication.py"
                "\n- save last"
                "\n"
            )
            continue

        if query.lower() == "save last":
            if last_result is None:
                print(
                    "No previous result available."
                )
                continue

            filename = (
                f"qtrustcode_result_"
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                f".json"
            )

            with open(
                filename,
                "w",
                encoding="utf-8",
            ) as fp:
                json.dump(
                    last_result,
                    fp,
                    indent=2,
                    default=str,
                )

            print(
                f"Saved results to {filename}"
            )
            continue

        if query.lower() in {
            "exit",
            "quit",
        }:
            print("\nQTrustCode session ended.")
            print(
                f"Queries processed: {session_queries}"
            )
            break

        if not query:
            continue

        session_queries += 1
        start = time.perf_counter()
        try:
            result = orchestrator.analyze(query)
        except Exception as exc:
            print(f"\nERROR: {exc}\n")
            continue
        last_result = result
        elapsed = round(
            time.perf_counter() - start,
            4,
        )

        print(
            f"\nRESULT [{datetime.now().strftime('%H:%M:%S')}]"
        )
        print("-" * 80)
        pprint(result)

        metadata = result.get(
            "orchestrator_metadata",
            {},
        )
        verification = result.get(
            "verification",
            {},
        )

        if metadata:
            print(
                f"Framework Version: "
                f"{metadata.get('version')}"
            )

        print(
            f"\nPipeline Status: "
            f"{result.get('pipeline_status')}"
        )
        print(
            f"Quantum Enabled: "
            f"{result.get('quantum_enabled')}"
        )
        if verification:
            print(
                f"Verification Status: "
                f"{verification.get('verification_status', verification.get('status'))}"
            )
            print(
                f"Reliability Score: "
                f"{verification.get('reliability_score', 'N/A')}"
            )

        performance = result.get(
            "performance",
            {},
        )

        if performance:
            print(
                "Agent Execution: "
                f"{performance.get('agent_execution_seconds', 0.0)}s"
            )
            print(
                "Total Execution: "
                f"{performance.get('total_execution_seconds', elapsed)}s"
            )
        else:
            print(
                f"Total Execution: {elapsed}s"
            )

        print(
            f"Session Queries: {session_queries}"
        )
        print()
