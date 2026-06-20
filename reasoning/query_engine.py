class QueryEngine:
    def __init__(
        self,
        repository,
        dependency_graph,
        function_graph,
        knowledge_graph,
        metrics=None,
    ):
        self.repository = repository
        self.dependency_graph = dependency_graph
        self.function_graph = function_graph
        self.knowledge_graph = knowledge_graph
        self.metrics = metrics or {}
        self._function_graph_stats = {
            "nodes": self.function_graph.number_of_nodes(),
            "edges": self.function_graph.number_of_edges(),
        }

    def resolve_file(
        self,
        target,
    ):
        target = target.strip().lower()
        target = target.replace("\\", "/")
        if target.endswith(".py"):
            target_stem = target[:-3]
        else:
            target_stem = target

        files = getattr(
            self.repository,
            "files",
            self.repository,
        )

        if hasattr(files, "keys"):
            file_paths = list(files.keys())
        else:
            file_paths = list(files)

        for file_path in file_paths:
            if file_path.lower() == target:
                return file_path

        matches = []

        for file_path in file_paths:
            normalized = file_path.lower()
            filename = file_path.split("/")[-1].lower()
            stem = filename.replace(".py", "")

            if (
                normalized == target
                or filename == target
                or stem == target
                or stem == target_stem
                or filename == f"{target_stem}.py"
                or normalized.endswith(f"/{target}")
                or normalized.endswith(f"/{target_stem}.py")
            ):
                matches.append(file_path)

        if len(matches) == 1:
            return matches[0]

        if len(matches) > 1:
            return {
                "error": f"Multiple files match '{target}': {matches}"
            }

        return None

    def resolve_function(
        self,
        target,
    ):
        target = target.strip()
        normalized = target.lower()

        graph_nodes = list(self.function_graph.nodes)

        # Exact node match first
        for node in graph_nodes:
            if str(node) == target:
                return node

        matches = []

        for node in graph_nodes:
            node_str = str(node)
            node_lower = node_str.lower()
            function_name = node_str.split(":")[-1].lower()

            if (
                node_lower == normalized
                or function_name == normalized
                or node_lower.endswith(f":{normalized}")
            ):
                matches.append(node)

        if len(matches) == 1:
            return matches[0]

        if len(matches) > 1:
            return {
                "error": (
                    f"Multiple functions match '{target}': {matches}"
                )
            }

        return None

    def find_dependencies(
        self,
        file_path,
    ):
        if file_path not in self.dependency_graph:
            return []

        return sorted(
            list(
                self.dependency_graph.successors(
                    file_path
                )
            )
        )

    def find_dependents(
        self,
        file_path,
    ):
        if file_path not in self.dependency_graph:
            return []

        return sorted(
            list(
                self.dependency_graph.predecessors(
                    file_path
                )
            )
        )

    def find_callers(
        self,
        function_name,
    ):
        target = self.resolve_function(function_name)

        if isinstance(target, dict):
            return target

        if target is None:
            return {
                "error": f"Function '{function_name}' could not be resolved",
                "graph_stats": self._function_graph_stats,
            }

        if target not in self.function_graph:
            return {
                "error": f"Function '{target}' is not present in the function graph",
                "graph_stats": self._function_graph_stats,
            }

        return {
            "function": str(target),
            "callers": sorted(
                str(node)
                for node in self.function_graph.predecessors(target)
            ),
            "graph_stats": self._function_graph_stats,
        }

    def find_callees(
        self,
        function_name,
    ):
        target = self.resolve_function(function_name)

        if isinstance(target, dict):
            return target

        if target is None:
            return {
                "error": f"Function '{function_name}' could not be resolved",
                "graph_stats": self._function_graph_stats,
            }

        if target not in self.function_graph:
            return {
                "error": f"Function '{target}' is not present in the function graph",
                "graph_stats": self._function_graph_stats,
            }

        return {
            "function": str(target),
            "callees": sorted(
                str(node)
                for node in self.function_graph.successors(target)
            ),
            "graph_stats": self._function_graph_stats,
        }

    def where_defined(
        self,
        function_name,
    ):
        return self.find_definition(
            function_name.split(":")[-1]
        )

    def find_definition(
        self,
        function_name,
    ):
        for node in self.knowledge_graph.nodes:
            if node.endswith(
                f":{function_name}"
            ):
                return node

        return None

    def trace_execution(
        self,
        start_function,
        visited=None,
    ):
        resolved = self.resolve_function(
            start_function
        )

        if isinstance(resolved, dict):
            return resolved

        if resolved is None:
            return {}

        start_function = resolved

        if visited is None:
            visited = set()

        if start_function in visited:
            return {}

        visited.add(start_function)

        trace = {}

        for callee in self.find_callees(
            start_function
        ):
            trace[callee] = self.trace_execution(
                callee,
                visited,
            )

        return trace

    def explain_function(
        self,
        function_name,
    ):
        definition = self.find_definition(
            function_name.split(":")[-1]
        )

        callers = self.find_callers(
            function_name
        )
        callees = self.find_callees(
            function_name
        )

        return {
            "function": function_name,
            "defined_in": definition,
            "callers": callers,
            "callees": callees,
            "execution_trace": self.trace_execution(
                function_name
            ),
        }

    def explain_file(
        self,
        file_path,
    ):
        file_data = self.repository.files.get(
            file_path
        )

        if file_data is None:
            return {
                "error": (
                    f"File '{file_path}' not found"
                )
            }

        return {
            "file": file_path,
            "imports": getattr(
                file_data,
                "imports",
                [],
            ),
            "functions": getattr(
                file_data,
                "functions",
                [],
            ),
            "classes": getattr(
                file_data,
                "classes",
                [],
            ),
            "dependencies": self.find_dependencies(
                file_path
            ),
            "dependents": self.find_dependents(
                file_path
            ),
        }

    def get_metrics(self):
        if self.metrics:
            return self.metrics

        metrics = getattr(self.repository, "metrics", None)

        if metrics:
            return metrics

        metrics = getattr(
            self.repository,
            "repository_metrics",
            None,
        )

        if metrics:
            return metrics

        metrics = getattr(
            self.repository,
            "file_metrics",
            None,
        )

        return metrics or {}

    def show_dead_files(self):
        metrics = self.get_metrics()
        dead = []

        if not metrics:
            for node in self.dependency_graph.nodes:
                if (
                    self.dependency_graph.in_degree(node) == 0
                    and self.dependency_graph.out_degree(node) == 0
                ):
                    dead.append(node)
            return sorted(dead)

        for file_path, data in metrics.items():
            if (
                data.get("fan_in", 0) == 0
                and data.get("fan_out", 0) == 0
            ):
                dead.append(file_path)

        return sorted(dead)

    def show_entry_points(self):
        metrics = self.get_metrics()
        entry_points = []

        if not metrics:
            for node in self.dependency_graph.nodes:
                if (
                    self.dependency_graph.in_degree(node) == 0
                    and self.dependency_graph.out_degree(node) > 0
                ):
                    entry_points.append(node)
            return sorted(entry_points)

        for file_path, data in metrics.items():
            if (
                data.get("fan_in", 0) == 0
                and data.get("fan_out", 0) > 0
            ):
                entry_points.append(file_path)

        return sorted(entry_points)

    def most_important_files(self, limit=10):
        metrics = self.get_metrics()
        scored = []

        if not metrics:
            for node in self.dependency_graph.nodes:
                score = (
                    self.dependency_graph.in_degree(node)
                    + self.dependency_graph.out_degree(node)
                )
                scored.append((node, round(score, 3)))

            scored.sort(
                key=lambda x: x[1],
                reverse=True,
            )
            return scored[:limit]

        for file_path, data in metrics.items():
            score = (
                data.get("centrality", 0)
                + data.get("pagerank", 0)
                + data.get("fan_in", 0)
            )
            scored.append((file_path, round(score, 3)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]

    def show_hotspots(self, limit=10):
        return self.most_important_files(limit)

    def why_file_important(self, file_path):
        target = self.resolve_file(file_path)

        if isinstance(target, dict):
            return target

        if target is None:
            return {
                "error": f"Could not resolve '{file_path}'"
            }

        metrics = self.get_metrics()

        return {
            "file": target,
            "metrics": metrics.get(target, {}),
            "depends_on": self.find_dependencies(target),
            "used_by": self.find_dependents(target),
        }

    def supported_commands(self):
        return [
            "show dependencies for <file>",
            "show dependents for <file>",
            "show callers of <function>",
            "show callees of <function>",
            "where is function <function>",
            "explain file <file>",
            "explain function <function>",
            "trace execution of <function>",
            "show dead files",
            "show entry points",
            "show hotspots",
            "show central files",
            "show important files",
            "what are the most important files",
            "why is <file> important",
        ]

    def query(
        self,
        text,
    ):
        query = text.lower().strip()
        if query == "help":
            return self.supported_commands()

        if query == "show dead files":
            return self.show_dead_files()

        if query == "show entry points":
            return self.show_entry_points()

        if query == "show hotspots":
            return self.show_hotspots()

        if query in {
            "show central files",
            "show important files",
            "show most important files",
        }:
            return self.most_important_files()

        if query == "what are the most important files":
            return self.most_important_files()

        if query.startswith("why is ") and query.endswith(" important"):
            name = text[7:-10].strip()
            return self.why_file_important(name)

        if query.startswith("show dependencies for "):
            name = text[len("show dependencies for "):].strip()
            target = self.resolve_file(name)
            if isinstance(target, dict):
                return target
            if target is None:
                return {
                    "error": f"Could not resolve '{name}'"
                }
            return self.find_dependencies(target)

        if query.startswith("show dependents for "):
            name = text[len("show dependents for "):].strip()
            target = self.resolve_file(name)
            if isinstance(target, dict):
                return target
            if target is None:
                return {
                    "error": f"Could not resolve '{name}'"
                }
            return self.find_dependents(target)

        if query.startswith("show callers of "):
            target = text[
                len("show callers of "):
            ].strip()
            resolved = self.resolve_function(target)
            if isinstance(resolved, dict):
                return resolved
            return self.find_callers(target)

        if query.startswith("show callees of "):
            target = text[
                len("show callees of "):
            ].strip()
            resolved = self.resolve_function(target)
            if isinstance(resolved, dict):
                return resolved
            return self.find_callees(target)

        if query.startswith("where is function "):
            target = text[
                len("where is function "):
            ].strip()
            return self.where_defined(target)

        if query.startswith("explain file "):
            name = text[len("explain file "):].strip()
            target = self.resolve_file(name)
            if isinstance(target, dict):
                return target
            if target is None:
                return {
                    "error": f"Could not resolve '{name}'"
                }
            return self.explain_file(target)

        if query.startswith("explain function "):
            target = text[len("explain function "):].strip()
            return self.explain_function(target)

        if query.startswith("trace execution of "):
            target = text[len("trace execution of "):].strip()
            return self.trace_execution(target)

        return {
            "error": (
                "Unknown query. Supported commands: "
                "show dependencies for <file>, "
                "show dependents for <file>, "
                "show callers of <function>, "
                "show callees of <function>, "
                "where is function <function>, "
                "explain file <file>, "
                "explain function <function>, "
                "trace execution of <function>, "
                "show dead files, show entry points, show hotspots, "
                "show central files, show important files, "
                "what are the most important files, why is <file> important"
            )
        }