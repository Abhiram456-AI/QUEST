

"""
QUEST: Quantum Evaluation of Software Trust

Phase 1:
Repository Intelligence Engine

Module:
Code Metrics Engine

Purpose:
Extracts quantitative software engineering metrics from source code.
These metrics form the classical feature foundation for QUEST trust vectors.

Outputs from this module feed:
- Trust Representation Engine
- QSVM classification
- QAOA prioritization
- Reliability prediction models
"""


import ast
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class CodeMetricResult:
    file_path: str
    lines_of_code: int
    function_count: int
    class_count: int
    cyclomatic_complexity: int
    average_function_complexity: float
    maintainability_score: float
    risk_score: float


class ComplexityVisitor(ast.NodeVisitor):
    """
    Computes approximate cyclomatic complexity
    using Python control flow structures.
    """

    def __init__(self):
        self.complexity = 1


    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)


    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)


    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)


    def visit_Try(self, node):
        self.complexity += len(node.handlers)
        self.generic_visit(node)


    def visit_BoolOp(self, node):
        self.complexity += len(node.values) - 1
        self.generic_visit(node)


class ModuleComplexityVisitor(ComplexityVisitor):
    """
    Computes module-level cyclomatic complexity by skipping function/class bodies.
    """
    def visit_FunctionDef(self, node):
        pass

    def visit_AsyncFunctionDef(self, node):
        pass

    def visit_ClassDef(self, node):
        pass



class CodeMetricsAnalyzer:
    """
    Generates measurable reliability indicators
    from software artifacts.
    """

    def analyze_file(self, file_path: str) -> CodeMetricResult:

        path = Path(file_path)

        try:
            source = path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            tree = ast.parse(source)

        except Exception as error:
            raise RuntimeError(
                f"Metric extraction failed: {error}"
            )

        loc = self.calculate_loc(source)

        functions = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]

        classes = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
        ]

        # Module-level cyclomatic complexity by skipping function/class bodies
        module_visitor = ModuleComplexityVisitor()
        module_visitor.visit(tree)
        module_complexity = module_visitor.complexity

        # Average complexity of individual functions
        total_func_complexity = 0
        for function in functions:
            visitor = ComplexityVisitor()
            visitor.visit(function)
            total_func_complexity += visitor.complexity

        avg_complexity = (
            total_func_complexity / len(functions)
            if functions
            else 0
        )

        # File-level total complexity is the sum of module-level complexity and all function complexities
        total_complexity = module_complexity + total_func_complexity

        maintainability = self.calculate_maintainability(
            loc,
            total_complexity
        )

        risk = self.calculate_risk_score(
            avg_complexity,
            maintainability
        )

        return CodeMetricResult(
            file_path=str(path),
            lines_of_code=loc,
            function_count=len(functions),
            class_count=len(classes),
            cyclomatic_complexity=total_complexity,
            average_function_complexity=avg_complexity,
            maintainability_score=maintainability,
            risk_score=risk
        )


    def calculate_loc(self, source: str) -> int:
        return len(
            [
                line
                for line in source.splitlines()
                if line.strip()
            ]
        )


    def calculate_maintainability(
        self,
        loc: int,
        complexity: int
    ) -> float:
        """
        Produces normalized maintainability estimate.
        Higher = better maintainability.
        """

        score = 100 - (
            complexity * 2
            + loc * 0.05
        )

        return max(
            0,
            round(score, 3)
        )


    def calculate_risk_score(
        self,
        complexity: float,
        maintainability: float
    ) -> float:
        """
        Generates preliminary reliability risk indicator.
        Later replaced by learned Trust Vector models.
        """

        risk = (
            complexity * 0.6
            + (100 - maintainability) * 0.4
        )

        return round(
            min(risk / 100, 1),
            4
        )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="QUEST Code Metrics Engine"
    )

    parser.add_argument(
        "--file",
        required=True,
        help="Python source file"
    )

    args = parser.parse_args()

    analyzer = CodeMetricsAnalyzer()

    result = analyzer.analyze_file(
        args.file
    )

    print(
        json.dumps(
            asdict(result),
            indent=4
        )
    )