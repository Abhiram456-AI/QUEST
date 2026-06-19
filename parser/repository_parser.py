from pathlib import Path

from parser.models import RepositoryMetadata
from parser.repository_scanner import (
    RepositoryScanner,
)
from parser.ast_parser import ASTParser


class RepositoryParser:

    def __init__(
        self,
        repository_path: str
    ):
        self.root = Path(repository_path)
        self.scanner = RepositoryScanner(
            repository_path
        )

    def parse(self) -> RepositoryMetadata:

        repository = RepositoryMetadata()

        files = (
            self.scanner
            .discover_python_files()
        )

        for file_path in files:

            metadata = ASTParser.parse(
                file_path=file_path,
                root_path=self.root
            )

            repository.files[
                metadata.path
            ] = metadata

        return repository