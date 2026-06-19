import networkx as nx


class FunctionGraphBuilder:

    def __init__(self):
        self.graph = nx.DiGraph()

    def build(self, repository):

        function_map = {}

        for (
            file_path,
            metadata
        ) in repository.files.items():

            for function_name in (
                metadata.functions
            ):
                function_map[
                    function_name
                ] = file_path

        for (
            file_path,
            metadata
        ) in repository.files.items():

            for (
                caller,
                callees
            ) in (
                metadata.function_calls.items()
            ):

                caller_node = (
                    f"{file_path}:{caller}"
                )

                self.graph.add_node(
                    caller_node
                )

                for callee in callees:

                    if (
                        callee
                        in function_map
                    ):

                        callee_file = (
                            function_map[
                                callee
                            ]
                        )

                        callee_node = (
                            f"{callee_file}:{callee}"
                        )

                        self.graph.add_edge(
                            caller_node,
                            callee_node
                        )

        return self.graph
