import json
from collections import defaultdict
from dataclasses import asdict

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

    parser = RepositoryParser(repository_path)

    repository = parser.parse()

    builder = DependencyGraphBuilder()
    graph = builder.build(repository)

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

    print("\nQUERY ENGINE READY")
    print("Type 'exit' to quit.\n")

    while True:
        query = input("QTrustCode > ").strip()

        if query.lower() in {
            "exit",
            "quit",
        }:
            break

        if not query:
            continue

        result = orchestrator.analyze(query)

        print("\nRESULT:")
        print(result)
        print()
