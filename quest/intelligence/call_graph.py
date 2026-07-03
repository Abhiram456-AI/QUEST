

"""
QUEST: Quantum Evaluation of Software Trust

Phase 1:
Repository Intelligence Engine

Module:
Call Graph Builder

Purpose:
Constructs a software knowledge graph G(V,E) representing
relationships between files, classes, functions, and calls.

This graph representation becomes the mathematical foundation
for Quantum Walk based reliability and risk propagation analysis.
"""


import ast
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List

import networkx as nx


@dataclass
class GraphMetrics:
    nodes: int
    edges: int
    density: float
    average_degree: float


@dataclass
class CallGraphResult:
    file_path: str
    graph_metrics: Dict
    nodes: List[str]
    edges: List[List[str]]


class CallGraphBuilder(ast.NodeVisitor):
    """
    Builds directed program dependency graphs.

    Nodes:
        - files
        - classes
        - functions

    Edges:
        - function calls
        - ownership relationships
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self.current_function = None
        self.current_class = None


    def visit_ClassDef(self, node):
        class_name = f"class:{node.name}"

        self.graph.add_node(
            class_name,
            type="class"
        )

        previous_class = self.current_class
        self.current_class = class_name

        self.generic_visit(node)

        self.current_class = previous_class


    def visit_FunctionDef(self, node):
        function_name = f"function:{node.name}"

        self.graph.add_node(
            function_name,
            type="function"
        )

        if self.current_class:
            self.graph.add_edge(
                self.current_class,
                function_name,
                relation="contains"
            )

        previous_function = self.current_function
        self.current_function = function_name

        self.generic_visit(node)

        self.current_function = previous_function


    def visit_Call(self, node):
        if not self.current_function:
            return

        called_function = None

        if isinstance(node.func, ast.Name):
            called_function = node.func.id

        elif isinstance(node.func, ast.Attribute):
            called_function = node.func.attr

        if called_function:
            target = f"function:{called_function}"

            self.graph.add_node(
                target,
                type="function"
            )

            self.graph.add_edge(
                self.current_function,
                target,
                relation="calls"
            )

        self.generic_visit(node)


    def build_graph(self, file_path: str) -> CallGraphResult:
        path = Path(file_path)

        try:
            source = path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            tree = ast.parse(source)

        except Exception as error:
            raise RuntimeError(
                f"Call graph construction failed: {error}"
            )

        file_node = f"file:{path.name}"

        self.graph.add_node(
            file_node,
            type="file"
        )

        self.visit(tree)

        for node in list(self.graph.nodes):
            if node != file_node:
                self.graph.add_edge(
                    file_node,
                    node,
                    relation="contains"
                )

        metrics = self.calculate_metrics()

        return CallGraphResult(
            file_path=str(path),
            graph_metrics=asdict(metrics),
            nodes=list(self.graph.nodes),
            edges=[
                list(edge)
                for edge in self.graph.edges
            ]
        )


    def calculate_metrics(self) -> GraphMetrics:
        node_count = self.graph.number_of_nodes()
        edge_count = self.graph.number_of_edges()

        if node_count == 0:
            average_degree = 0
        else:
            degrees = dict(self.graph.degree())
            average_degree = sum(degrees.values()) / node_count

        return GraphMetrics(
            nodes=node_count,
            edges=edge_count,
            density=nx.density(self.graph),
            average_degree=average_degree
        )


    def export_graphml(self, output_path: str):
        nx.write_graphml(
            self.graph,
            output_path
        )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="QUEST Call Graph Builder"
    )

    parser.add_argument(
        "--file",
        required=True,
        help="Python source file"
    )

    parser.add_argument(
        "--export",
        required=False,
        help="Optional GraphML export path"
    )

    args = parser.parse_args()

    builder = CallGraphBuilder()

    result = builder.build_graph(args.file)

    if args.export:
        builder.export_graphml(args.export)

    print(
        json.dumps(
            asdict(result),
            indent=4
        )
    )