import networkx as nx


class KnowledgeGraphBuilder:

    def build(self, repository):

        graph = nx.MultiDiGraph()

        # File, function, class and import relationships
        for path, metadata in repository.files.items():

            graph.add_node(
                path,
                type="file"
            )

            # Functions defined in file
            for func in metadata.functions:

                function_node = (
                    f"{path}:{func}"
                )

                graph.add_node(
                    function_node,
                    type="function"
                )

                graph.add_edge(
                    path,
                    function_node,
                    relation="DEFINES"
                )

            # Classes defined in file
            for cls in metadata.classes:

                class_node = (
                    f"{path}:{cls}"
                )

                graph.add_node(
                    class_node,
                    type="class"
                )

                graph.add_edge(
                    path,
                    class_node,
                    relation="DEFINES"
                )

            # Imported modules
            for imp in metadata.imports:

                if not graph.has_node(imp):
                    graph.add_node(
                        imp,
                        type="module"
                    )

                graph.add_edge(
                    path,
                    imp,
                    relation="IMPORTS"
                )

        # Function call relationships
        for path, metadata in repository.files.items():

            for source_function, called_functions in (
                metadata.function_calls.items()
            ):

                source_node = (
                    f"{path}:{source_function}"
                )

                for called_function in called_functions:

                    target_path = None

                    for file_path, file_metadata in (
                        repository.files.items()
                    ):

                        if called_function in (
                            file_metadata.functions
                        ):
                            target_path = file_path
                            break

                    if target_path is None:
                        continue

                    target_node = (
                        f"{target_path}:{called_function}"
                    )

                    graph.add_edge(
                        source_node,
                        target_node,
                        relation="CALLS"
                    )

        return graph