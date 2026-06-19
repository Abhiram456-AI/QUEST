import json
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


if __name__ == "__main__":

    repository_path = input(
        "Repository Path: "
    )

    parser = RepositoryParser(
        repository_path
    )

    repository = parser.parse()

    builder = DependencyGraphBuilder()
    graph = builder.build(repository)

    print("\nDEPENDENCY EDGES:\n")

    for source, target in graph.edges():
        print(f"{source} ---> {target}")

    result = {
        path: asdict(metadata)
        for path, metadata
        in repository.files.items()
    }

    print(
        json.dumps(
            result,
            indent=4
        )
    )

    metrics_engine = RepositoryMetrics(
        graph,
        repository
    )

    metrics = metrics_engine.compute()

    print("\nREPOSITORY METRICS\n")

    for file, values in metrics.items():
        print(file)
        print(values)
        print()

    function_builder = (
        FunctionGraphBuilder()
    )

    function_graph = (
        function_builder.build(
            repository
        )
    )

    print(
        "\nFUNCTION CALL EDGES:\n"
    )
    print(
        f"Function Nodes: {function_graph.number_of_nodes()}"
    )

    print(
        f"Function Edges: {function_graph.number_of_edges()}\n"
    )

    for (
        source,
        target
    ) in function_graph.edges():

        print(
            f"{source} ---> {target}"
        )