import ast
from pathlib import Path
from parser.models import FileMetadata


class ASTParser:

    @staticmethod
    def parse(
        file_path: Path,
        root_path: Path
    ) -> FileMetadata:

        metadata = FileMetadata(
            path=str(
                file_path.relative_to(root_path)
            )
        )
        # called_functions removed

        try:
            source = file_path.read_text(
                encoding="utf-8"
            )

            tree = ast.parse(source)
            metadata.function_calls = {}

        except Exception:
            return metadata

        for node in ast.walk(tree):

            if isinstance(
                node,
                ast.FunctionDef
            ):
                metadata.functions.append(
                    node.name
                )

                metadata.defined_functions[
                    node.name
                ] = metadata.path

                metadata.function_calls[
                    node.name
                ] = []

                for child in ast.walk(node):

                    if isinstance(
                        child,
                        ast.Call
                    ):

                        if isinstance(
                            child.func,
                            ast.Name
                        ):
                            metadata.function_calls[
                                node.name
                            ].append(
                                child.func.id
                            )

                        elif isinstance(
                            child.func,
                            ast.Attribute
                        ):
                            metadata.function_calls[
                                node.name
                            ].append(
                                child.func.attr
                            )

                metadata.function_calls[
                    node.name
                ] = list(
                    dict.fromkeys(
                        metadata.function_calls[
                            node.name
                        ]
                    )
                )

            elif isinstance(
                node,
                ast.AsyncFunctionDef
            ):
                metadata.functions.append(
                    node.name
                )

                metadata.defined_functions[
                    node.name
                ] = metadata.path

                metadata.function_calls[
                    node.name
                ] = []

                for child in ast.walk(node):

                    if isinstance(
                        child,
                        ast.Call
                    ):

                        if isinstance(
                            child.func,
                            ast.Name
                        ):
                            metadata.function_calls[
                                node.name
                            ].append(
                                child.func.id
                            )

                        elif isinstance(
                            child.func,
                            ast.Attribute
                        ):
                            metadata.function_calls[
                                node.name
                            ].append(
                                child.func.attr
                            )

                metadata.function_calls[
                    node.name
                ] = list(
                    dict.fromkeys(
                        metadata.function_calls[
                            node.name
                        ]
                    )
                )

            elif isinstance(
                node,
                ast.ClassDef
            ):
                metadata.classes.append(
                    node.name
                )

            elif isinstance(
                node,
                ast.Import
            ):
                for alias in node.names:
                    metadata.imports.append(
                        alias.name
                    )

            elif isinstance(
                node,
                ast.ImportFrom
            ):
                if node.module:
                    metadata.imports.append(
                        node.module
                    )

        # Remove metadata.called_functions assignment
        return metadata