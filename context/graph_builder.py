import networkx as nx


class DependencyGraphBuilder:

    def __init__(self):
        self.graph = nx.DiGraph()

    def build(self, repository):

        repository_files = set(
            repository.files.keys()
        )

        for file_path, metadata in (
            repository.files.items()
        ):

            self.graph.add_node(file_path)

            for module in metadata.imports:

                imported_file = (
                    module.replace(".", "/")
                    + ".py"
                )

                if imported_file in repository_files:
                    self.graph.add_edge(
                        file_path,
                        imported_file
                    )

        return self.graph