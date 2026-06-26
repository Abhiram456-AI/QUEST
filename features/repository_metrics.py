import networkx as nx


class RepositoryMetrics:

    def __init__(self, graph, repository):
        self.graph = graph
        self.repository = repository

    def compute(self):

        metrics = {}

        if self.repository is None:
            return {
                "__repository_summary__": {
                    "repository_files": 0,
                    "graph_nodes": 0,
                    "graph_edges": 0,
                    "metrics_generated": 0,
                    "graph_available": (
                        self.graph is not None
                    ),
                    "coverage_ratio": 0.0,
                }
            }

        if (
            self.graph is None
            or self.graph.number_of_nodes() == 0
        ):
            pagerank = {}
            centrality = {}
        else:
            try:
                pagerank = nx.pagerank(
                    self.graph
                )
            except Exception:
                pagerank = {}

            try:
                centrality = (
                    nx.degree_centrality(
                        self.graph
                    )
                )
            except Exception:
                centrality = {}

        repository_files = getattr(
            self.repository,
            "files",
            {},
        ) or {}

        graph = self.graph
        has_graph = graph is not None

        graph_nodes = (
            graph.number_of_nodes()
            if has_graph
            else 0
        )
        graph_edges = (
            graph.number_of_edges()
            if has_graph
            else 0
        )

        for file_path, metadata in (
            repository_files.items()
        ):
            fan_in = (
                graph.in_degree(file_path)
                if has_graph
                and graph.has_node(file_path)
                else 0
            )

            fan_out = (
                graph.out_degree(file_path)
                if has_graph
                and graph.has_node(file_path)
                else 0
            )

            dependency_load = (
                fan_in + fan_out
            )

            instability = round(
                fan_out /
                max(
                    dependency_load,
                    1,
                ),
                3,
            )

            centrality_score = float(
                centrality.get(
                    file_path,
                    0.0,
                )
            )

            pagerank_score = float(
                pagerank.get(
                    file_path,
                    0.0,
                )
            )

            metrics[file_path] = {
                "fan_in": fan_in,

                "fan_out": fan_out,

                "centrality": centrality_score,

                "pagerank": pagerank_score,

                "function_count":
                    len(
                        getattr(
                            metadata,
                            "functions",
                            [],
                        )
                    ),

                "class_count":
                    len(
                        getattr(
                            metadata,
                            "classes",
                            [],
                        )
                    ),

                "import_count": len(
                    getattr(
                        metadata,
                        "imports",
                        [],
                    )
                ),
                "instability": instability,
                "dependency_load": dependency_load,
                "has_graph_node": (
                    has_graph
                    and graph.has_node(file_path)
                )
            }

        file_metrics_count = len(metrics)

        metrics["__repository_summary__"] = {
            "repository_files": len(
                repository_files
            ),
            "graph_nodes": graph_nodes,
            "graph_edges": graph_edges,
            "metrics_generated": (
                file_metrics_count
            ),
            "graph_available": has_graph,
            "coverage_ratio": round(
                graph_nodes /
                max(
                    len(repository_files),
                    1,
                ),
                3,
            ),
        }

        return metrics