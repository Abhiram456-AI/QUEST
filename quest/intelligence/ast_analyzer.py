

"""
QUEST: Quantum Evaluation of Software Trust

Phase 1:
Repository Intelligence Engine

Module:
AST Analyzer

Purpose:
Transforms source code into structured program representations
including functions, classes, imports, inheritance relationships,
and function call dependencies.

The extracted representations become inputs for dependency graphs,
software metrics, and trust feature construction.
"""


import ast
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional


@dataclass
class FunctionInfo:
    name: str
    arguments: int
    start_line: int
    end_line: int
    length: int
    calls: List[str]


@dataclass
class ClassInfo:
    name: str
    methods: List[str]
    inheritance: List[str]
    start_line: int


@dataclass
class ASTResult:
    file_path: str
    imports: List[str]
    functions: List[Dict]
    classes: List[Dict]


class ASTAnalyzer(ast.NodeVisitor):
    """
    Extracts semantic structures from Python source code.
    """

    def __init__(self):
        self.imports = []
        self.functions = []
        self.classes = []


    def visit_Import(self, node):
        for item in node.names:
            self.imports.append(item.name)

        self.generic_visit(node)


    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.append(node.module)

        self.generic_visit(node)


    def visit_FunctionDef(self, node):
        calls = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):

                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)

                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)

        function = FunctionInfo(
            name=node.name,
            arguments=len(node.args.args),
            start_line=node.lineno,
            end_line=getattr(node, "end_lineno", node.lineno),
            length=getattr(node, "end_lineno", node.lineno) - node.lineno + 1,
            calls=list(set(calls))
        )

        self.functions.append(asdict(function))

        self.generic_visit(node)


    def visit_ClassDef(self, node):
        methods = []
        inheritance = []

        for base in node.bases:
            if isinstance(base, ast.Name):
                inheritance.append(base.id)

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)

        class_info = ClassInfo(
            name=node.name,
            methods=methods,
            inheritance=inheritance,
            start_line=node.lineno
        )

        self.classes.append(asdict(class_info))

        self.generic_visit(node)


    def analyze_file(self, file_path: str) -> ASTResult:
        source_path = Path(file_path)

        try:
            source = source_path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            tree = ast.parse(source)

        except SyntaxError:
            raise ValueError(
                f"Unable to parse Python file: {file_path}"
            )

        self.visit(tree)

        return ASTResult(
            file_path=str(source_path),
            imports=self.imports,
            functions=self.functions,
            classes=self.classes
        )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="QUEST AST Analyzer"
    )

    parser.add_argument(
        "--file",
        required=True,
        help="Python source file path"
    )

    args = parser.parse_args()

    analyzer = ASTAnalyzer()

    result = analyzer.analyze_file(args.file)

    print(
        json.dumps(
            asdict(result),
            indent=4
        )
    )