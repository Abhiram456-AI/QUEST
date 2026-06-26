
class QueryEngine:
    def __init__(
        self,
        repository,
        dependency_graph,
        function_graph,
        knowledge_graph,
        metrics=None,
        dependency_path_engine=None,
        function_path_engine=None,
        knowledge_path_engine=None,
        impact_engine=None,
        coupling_engine=None,
        risk_engine=None,
        execution_engine=None,
    ):
        self.repository = repository
        self.dependency_graph = dependency_graph
        self.function_graph = function_graph
        self.knowledge_graph = knowledge_graph
        self.metrics = metrics or {}
        # Backward-compatible aliases used by the multi-agent layer
        self.repository_metrics = self.metrics

        files = getattr(
            self.repository,
            "files",
            self.repository,
        )

        if hasattr(files, "keys"):
            self.repository_nodes = sorted(files.keys())
        else:
            self.repository_nodes = sorted(files)
        self.graph = self.dependency_graph
        self.dependency_path_engine = (
            dependency_path_engine
        )
        self.function_path_engine = (
            function_path_engine
        )
        self.knowledge_path_engine = (
            knowledge_path_engine
        )
        self.impact_engine = (
            impact_engine
        )
        self.coupling_engine = (
            coupling_engine
        )
        self.risk_engine = (
            risk_engine
        )
        self.execution_engine = (
            execution_engine
        )
        # Convenience context bundle for agents and future integrations
        self.context = {
            "repository": self.repository,
            "dependency_graph": self.dependency_graph,
            "function_graph": self.function_graph,
            "knowledge_graph": self.knowledge_graph,
            "repository_metrics": self.repository_metrics,
            "impact_engine": self.impact_engine,
            "coupling_engine": self.coupling_engine,
            "risk_engine": self.risk_engine,
            "execution_engine": self.execution_engine,
        }
        # Default quantum context entries for integration
        self.context.setdefault("qaoa_result", None)
        self.context.setdefault("qsvm_result", None)
        self.context.setdefault("quantum_walk_result", None)
        self.context.setdefault("vqnn_result", None)
        self.context.setdefault("quantum_enabled", False)
        # Instance attributes for quantum result synchronization
        self.qaoa_result = None
        self.qsvm_result = None
        self.quantum_walk_result = None
        self.vqnn_result = None
        self._function_graph_stats = {
            "nodes": (
                self.function_graph.number_of_nodes()
                if self.function_graph is not None else 0
            ),
            "edges": (
                self.function_graph.number_of_edges()
                if self.function_graph is not None else 0
            ),
        }
        self.context["repository_nodes"] = (
            self.repository_nodes
        )
        self.context["repository_node_count"] = len(
            self.repository_nodes
        )

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
        if self.function_graph is None:
            return None

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
        if self.knowledge_graph is None:
            return None
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

        callees = self.find_callees(
            start_function
        )

        if isinstance(callees, dict):
            callees = callees.get(
                "callees",
                [],
            )

        for callee in callees:
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
        files = getattr(
            self.repository,
            "files",
            self.repository,
        )

        file_data = files.get(
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
            "show dependencies of <file>",
            "show dependency chain of <file>",
            "show dependents for <file>",
            "show dependents of <file>",
            "what depends on <file>",
            "what does <file> depend on",
            "show callers of <function>",
            "show callees of <function>",
            "where is function <function>",
            "find path from <file> to <file>",
            "show impact of <file>",
            "show impacted by <file>",
            "blast radius of <file>",
            "criticality of <file>",
            "show ancestors of <file>",
            "show descendants of <file>",
            "explain file <file>",
            "explain function <function>",
            "trace execution of <function>",
            "find execution path from <function> to <function>",
            "show dead files",
            "show entry points",
            "show hotspots",
            "show central files",
            "show important files",
            "what are the most important files",
            "why is <file> important",
            "show coupling of <file>",
            "show instability of <file>",
            "most coupled modules",
            "repository coupling summary",
            "show risk of <file>",
            "show risky modules",
            "highest risk modules",
            "most risky modules",
            "top risky modules",
            "repository risk summary",
            "explain <file>",
            "risk of <file>",
        ]

    def get_repository_nodes(self):
        return list(self.repository_nodes)
    
    
    def get_context(self):
        # Copy context and synchronize quantum results
        context = dict(self.context)
        # Synchronize quantum result attributes into context copy
        for name in ("qaoa_result", "qsvm_result", "quantum_walk_result", "vqnn_result"):
            value = getattr(self, name, None)
            if value is not None:
                context[name] = value
        context["quantum_enabled"] = any(
            context.get(name) is not None
            for name in (
                "qaoa_result",
                "qsvm_result",
                "quantum_walk_result",
                "vqnn_result",
            )
        )
        context["repository_nodes"] = list(self.repository_nodes)
        context["repository_node_count"] = len(self.repository_nodes)
        return context

    def update_quantum_results(
        self,
        qaoa_result=None,
        qsvm_result=None,
        quantum_walk_result=None,
        vqnn_result=None,
    ):
        """Synchronize quantum module outputs into the shared query context."""
        updates = {
            "qaoa_result": qaoa_result,
            "qsvm_result": qsvm_result,
            "quantum_walk_result": quantum_walk_result,
            "vqnn_result": vqnn_result,
        }
        for name, value in updates.items():
            if value is not None:
                setattr(self, name, value)
                self.context[name] = value
        self.context["quantum_enabled"] = any(
            self.context.get(name) is not None
            for name in updates
        )
        return self.context

    def explain_path(
        self,
        source,
        target,
    ):
        if self.dependency_path_engine is None:
            return {
                "error": "Dependency path engine not available"
            }

        resolved_source = self.resolve_file(source)
        if isinstance(resolved_source, dict):
            return resolved_source

        resolved_target = self.resolve_file(target)
        if isinstance(resolved_target, dict):
            return resolved_target

        if resolved_source is None:
            return {
                "error": f"Could not resolve '{source}'"
            }

        if resolved_target is None:
            return {
                "error": f"Could not resolve '{target}'"
            }

        return self.dependency_path_engine.find_path(
            resolved_source,
            resolved_target,
        )

    def impact_analysis(
        self,
        node,
    ):
        if self.dependency_path_engine is None:
            return {
                "error": "Dependency path engine not available"
            }

        target = self.resolve_file(node)

        if isinstance(target, dict):
            return target

        if target is None:
            return {
                "error": f"Could not resolve '{node}'"
            }

        return (
            self.dependency_path_engine.impact_analysis(
                target
            )
        )

    def show_ancestors(
        self,
        node,
    ):
        if self.dependency_path_engine is None:
            return []

        target = self.resolve_file(node)

        if isinstance(target, dict):
            return target

        if target is None:
            return {
                "error": f"Could not resolve '{node}'"
            }

        return (
            self.dependency_path_engine.get_ancestors(
                target
            )
        )

    def show_descendants(
        self,
        node,
    ):
        if self.dependency_path_engine is None:
            return []

        target = self.resolve_file(node)

        if isinstance(target, dict):
            return target

        if target is None:
            return {
                "error": f"Could not resolve '{node}'"
            }

        return (
            self.dependency_path_engine.get_descendants(
                target
            )
        )
    
    def coupling_analysis(
        self,
        node,
    ):
        if self.coupling_engine is None:
            return {
                "error": "Coupling engine not available"
            }
        target = self.resolve_file(node)
        
        if isinstance(target, dict):
            return target
        if target is None:
            return {
                "error": f"Could not resolve '{node}'"
            }
        return self.coupling_engine.coupling_report(
            target
        )

    def instability_analysis(
        self,
        node,
    ):
        if self.coupling_engine is None:
            return {
                "error": "Coupling engine not available"
                }
        target = self.resolve_file(node)
        if isinstance(target, dict):
            return target
        if target is None:
            return {
                "error": f"Could not resolve '{node}'"
            }
        return {
            "node": target,
            "instability": self.coupling_engine.instability(target),
        }

    def risk_analysis(
        self,
        node,
    ):
        if self.risk_engine is None:
            return {
                "error": "Risk engine not available"
            }

        target = self.resolve_file(node)

        if isinstance(target, dict):
            return target

        if target is None:
            return {
                "error": f"Could not resolve '{node}'"
            }

        return self.risk_engine.risk_report(
            target
        )

    def normalize_aliases(
        self,
        text,
    ):
        query = text.strip().lower()
        aliases = {
            "show dependencies of ": "show dependencies for ",
            "show dependency chain of ": "show dependencies for ",
            "show dependents of ": "show dependents for ",
            "show impacted by ": "show impact of ",
            "what depends on ": "show dependents for ",
            "show instability for ": "show instability of ",
            "show coupling for ": "show coupling of ",
            "show risk for ": "show risk of ",
            "highest risk modules": "show risky modules",
            "most risky modules": "show risky modules",
            "top risky modules": "show risky modules",
            "explain ": "explain file ",
            "risk of ": "show risk of ",
            "dependencies of ": "show dependencies for ",
            "dependents of ": "show dependents for ",
        }
        for alias, canonical in aliases.items():
            if query.startswith(alias):
                return canonical + text[len(alias):]

        if query.startswith("what does ") and query.endswith(" depend on"):
            target = text[len("what does "):-len(" depend on")].strip()
            return f"show dependencies for {target}"

        return text

    def query(
        self,
        text,
    ):
        text = self.normalize_aliases(text)
        query = text.lower().strip()
        self.context["last_query"] = text
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
            target = text[len("show callers of "):].strip()

            if self.execution_engine is not None:
                resolved = self.resolve_function(target)
                if isinstance(resolved, dict):
                    return resolved
                if resolved is None:
                    return {
                        "error": f"Could not resolve '{target}'"
                    }
                return self.execution_engine.callers_of(resolved)

            return self.find_callers(target)

        if query.startswith("show callees of "):
            target = text[len("show callees of "):].strip()

            if self.execution_engine is not None:
                resolved = self.resolve_function(target)
                if isinstance(resolved, dict):
                    return resolved
                if resolved is None:
                    return {
                        "error": f"Could not resolve '{target}'"
                    }
                return self.execution_engine.callees_of(resolved)

            return self.find_callees(target)

        if query.startswith("find path from "):
            remainder = text[len("find path from "):]

            if " to " not in remainder:
                return {
                    "error": "Use: find path from <file> to <file>"
                }

            source, target = remainder.split(
                " to ",
                1,
            )

            return self.explain_path(
                source.strip(),
                target.strip(),
            )

        if query.startswith("show impact of "):
            target = text[len("show impact of "):].strip()
            return self.impact_analysis(target)
        
        if query.startswith("blast radius of "):
            target = text[len("blast radius of "):].strip()
            resolved = self.resolve_file(target)
            if isinstance(resolved, dict):
                return resolved
            if resolved is None:
                return {
                    "error": f"Could not resolve '{target}'"
                }
            if self.impact_engine is None:
                return {
                    "error": "Impact engine not available"
                }
            return self.impact_engine.get_change_blast_radius(
                resolved
            )

        if query.startswith("criticality of "):
            target = text[len("criticality of "):].strip()
            resolved = self.resolve_file(target)
            if isinstance(resolved, dict):
                return resolved
            if resolved is None:
                return {
                    "error": f"Could not resolve '{target}'"
                }
            if self.impact_engine is None:
                return {
                    "error": "Impact engine not available"
                }
            return {
                "node": resolved,
                "criticality": self.impact_engine.get_criticality(
                    resolved
                ),
            }
        
        if query.startswith("show coupling of "):
            target = text[len("show coupling of "):].strip()
            return self.coupling_analysis(target)

        if query.startswith("show instability of "):
            target = text[len("show instability of "):].strip()
            return self.instability_analysis(target)

        if query == "most coupled modules":
            if self.coupling_engine is None:
                return {
                    "error": "Coupling engine not available"
                }
            return self.coupling_engine.central_modules()

        if query == "repository coupling summary":
            if self.coupling_engine is None:
                return {
                    "error": "Coupling engine not available"
                }
            return self.coupling_engine.repository_summary()

        if query.startswith("show risk of "):
            target = text[len("show risk of "):].strip()
            return self.risk_analysis(target)

        if query in {
            "show risky modules",
            "highest risk modules",
            "most risky modules",
            "top risky modules",
        }:
            if self.risk_engine is None:
                return {
                    "error": "Risk engine not available"
                }
            return self.risk_engine.high_risk_modules()

        if query == "repository risk summary":
            if self.risk_engine is None:
                return {
                    "error": "Risk engine not available"
                }
            return self.risk_engine.repository_summary()

        if query.startswith("show ancestors of "):
            target = text[len("show ancestors of "):].strip()
            return self.show_ancestors(target)

        if query.startswith("show descendants of "):
            target = text[len("show descendants of "):].strip()
            return self.show_descendants(target)

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

            if self.execution_engine is not None:
                resolved = self.resolve_function(target)
                if isinstance(resolved, dict):
                    return resolved
                if resolved is None:
                    return {
                        "error": f"Could not resolve '{target}'"
                    }
                return self.execution_engine.execution_trace(
                    resolved
                )

            return self.trace_execution(target)

        if query.startswith("find execution path from "):
            if self.execution_engine is None:
                return {
                    "error": "Execution engine not available"
                }

            remainder = text[len("find execution path from "):]

            if " to " not in remainder:
                return {
                    "error": (
                        "Use: find execution path from <function> to <function>"
                    )
                }

            source, target = remainder.split(
                " to ",
                1,
            )

            source = self.resolve_function(
                source.strip()
            )
            target = self.resolve_function(
                target.strip()
            )

            if isinstance(source, dict):
                return source
            if isinstance(target, dict):
                return target
            if source is None or target is None:
                return {
                    "error": "Could not resolve one or both functions"
                }

            return self.execution_engine.execution_path(
                source,
                target,
            )

        return {
            "error": "Unknown query.",
            "supported_commands": self.supported_commands(),
        }