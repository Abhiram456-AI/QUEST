import networkx as nx


class RepositoryMetrics:

    def __init__(self, graph, repository):
        self.graph = graph
        self.repository = repository

    def compute(self):

        metrics = {}

        pagerank = nx.pagerank(self.graph)
        centrality = nx.degree_centrality(
            self.graph
        )

        for file_path, metadata in (
            self.repository.files.items()
        ):

            metrics[file_path] = {
                "fan_in":
                    self.graph.in_degree(
                        file_path
                    ),

                "fan_out":
                    self.graph.out_degree(
                        file_path
                    ),

                "centrality":
                    centrality.get(
                        file_path,
                        0
                    ),

                "pagerank":
                    pagerank.get(
                        file_path,
                        0
                    ),

                "function_count":
                    len(
                        metadata.functions
                    ),

                "class_count":
                    len(
                        metadata.classes
                    ),

                "import_count":
                    len(
                        metadata.imports
                    )
            }

        return metrics