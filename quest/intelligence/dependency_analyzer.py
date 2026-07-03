

"""
QUEST: Quantum Evaluation of Software Trust

Phase 1:
Repository Intelligence Engine

Module:
Dependency Analyzer

Purpose:
Builds measurable software dependency relationships from AST outputs.
Creates file, import, class inheritance, and function call dependency mappings
required for graph construction and later Quantum Walk risk propagation.
"""


import ast
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List


@dataclass
class DependencyResult:
    file_path: str
    imports: List[str]
    function_dependencies: Dict[str, List[str]]
    class_dependencies: Dict[str, List[str]]
    dependency_count: int


class DependencyAnalyzer(ast.NodeVisitor):
    """
    Extracts structural dependencies from Python source files.
    """

    def __init__(self):
        self.imports = []
        self.function_dependencies = {}
        self.class_dependencies = {}


    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)

        self.generic_visit(node)


    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.append(node.module)

        self.generic_visit(node)


    def visit_FunctionDef(self, node):
        dependencies = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):

                if isinstance(child.func, ast.Name):
                    dependencies.append(child.func.id)

                elif isinstance(child.func, ast.Attribute):
                    dependencies.append(child.func.attr)

        self.function_dependencies[node.name] = list(
            set(dependencies)
        )

        self.generic_visit(node)


    def visit_ClassDef(self, node):
        dependencies = []

        for base in node.bases:

            if isinstance(base, ast.Name):
                dependencies.append(base.id)

            elif isinstance(base, ast.Attribute):
                dependencies.append(base.attr)

        self.class_dependencies[node.name] = dependencies

        self.generic_visit(node)


    def analyze_file(self, file_path: str) -> DependencyResult:
        path = Path(file_path)

        try:
            source = path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            tree = ast.parse(source)

        except Exception as error:
            raise RuntimeError(
                f"Dependency analysis failed for {file_path}: {error}"
            )

        self.visit(tree)

        dependency_count = (
            len(self.imports)
            + sum(len(v) for v in self.function_dependencies.values())
            + sum(len(v) for v in self.class_dependencies.values())
        )

        return DependencyResult(
            file_path=str(path),
            imports=list(set(self.imports)),
            function_dependencies=self.function_dependencies,
            class_dependencies=self.class_dependencies,
            dependency_count=dependency_count
        )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="QUEST Dependency Analyzer"
    )

    parser.add_argument(
        "--file",
        required=True,
        help="Python source file"
    )

    args = parser.parse_args()

    analyzer = DependencyAnalyzer()

    result = analyzer.analyze_file(args.file)

    print(
        json.dumps(
            asdict(result),
            indent=4
        )
    )