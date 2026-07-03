"""
QUEST: Quantum Evaluation of Software Trust

Phase 1:
Repository Intelligence Engine

Module:
Repository Scanner

Purpose:
Transforms raw software repositories into structured,
measurable metadata for downstream trust evaluation.

Author:
QUEST Research Framework
"""


from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List
import hashlib
import json
import os


# Directories ignored during analysis
IGNORE_DIRS = {
    ".git",
    "__pycache__",
    ".idea",
    ".vscode",

    # Python environments
    "venv",
    ".venv",
    "env",
    ".env",
    "ENV",

    # Generated environments with suffixes
    ".venv-1",
    ".venv-2",

    # Dependency folders
    "node_modules",
    "site-packages",

    # Build/cache outputs
    "dist",
    "build",
    "outputs",
    ".pytest_cache",
    ".mypy_cache",

    # OS metadata
    ".DS_Store",
}


LANGUAGE_MAP = {
    ".py": "Python",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
}


@dataclass
class FileMetadata:
    """
    Represents measurable properties
    of an individual software artifact.
    """

    path: str
    language: str
    extension: str
    size_bytes: int
    lines_of_code: int
    file_hash: str



@dataclass
class RepositoryMetadata:
    """
    Repository-level representation.
    """

    repository: str
    total_files: int
    total_loc: int
    languages: Dict[str, int]
    files: List[Dict]



class RepositoryScanner:


    def __init__(self, repo_path: str):

        self.repo_path = Path(repo_path)

        if not self.repo_path.exists():
            raise FileNotFoundError(
                f"Repository not found: {repo_path}"
            )

        self.files = []



    def scan(self) -> RepositoryMetadata:
        """
        Executes complete repository analysis.
        """

        language_count = {}
        total_loc = 0


        for file_path in self.repo_path.rglob("*"):


            if self._should_ignore(file_path):
                continue


            if file_path.is_file():

                extension = file_path.suffix


                if extension not in LANGUAGE_MAP:
                    continue


                metadata = self._analyze_file(file_path)


                # Ignore empty source files to prevent
                # artificial zero-risk samples from contaminating
                # QUEST trust feature generation.
                if metadata.size_bytes == 0 or metadata.lines_of_code == 0:
                    continue


                self.files.append(
                    asdict(metadata)
                )


                total_loc += metadata.lines_of_code


                language_count[
                    metadata.language
                ] = language_count.get(
                    metadata.language,
                    0
                ) + 1



        return RepositoryMetadata(

            repository=self.repo_path.name,

            total_files=len(self.files),

            total_loc=total_loc,

            languages=language_count,

            files=self.files
        )




    def _analyze_file(
        self,
        file_path: Path

    ) -> FileMetadata:


        try:

            content = file_path.read_text(
                encoding="utf-8",
                errors="ignore"
            )


        except Exception:

            content = ""



        loc = len(
            [
                line
                for line in content.splitlines()
                if line.strip()
            ]
        )


        return FileMetadata(

            path=str(
                file_path.relative_to(
                    self.repo_path
                )
            ),

            language=LANGUAGE_MAP[
                file_path.suffix
            ],

            extension=file_path.suffix,

            size_bytes=os.path.getsize(
                file_path
            ),

            lines_of_code=loc,

            file_hash=self._hash_file(
                file_path
            )
        )




    def _hash_file(
        self,
        file_path: Path

    ) -> str:


        sha = hashlib.sha256()


        try:

            with open(
                file_path,
                "rb"

            ) as file:


                while chunk := file.read(4096):

                    sha.update(chunk)



        except Exception:

            return ""


        return sha.hexdigest()




    def _should_ignore(
        self,
        path: Path

    ) -> bool:
        """
        Determines whether a path should be excluded
        from repository intelligence extraction.

        Prevents virtual environments, dependencies,
        generated files, and external packages from
        contaminating QUEST research metrics.
        """

        parts = set(path.parts)

        if parts.intersection(IGNORE_DIRS):
            return True

        for part in path.parts:
            if part.startswith(".venv"):
                return True

        return False





if __name__ == "__main__":


    import argparse


    parser = argparse.ArgumentParser(
        description=
        "QUEST Repository Scanner"
    )


    parser.add_argument(
        "--repo",
        required=True,
        help="Path to repository"
    )


    args = parser.parse_args()



    scanner = RepositoryScanner(
        args.repo
    )


    result = scanner.scan()


    print(
        json.dumps(
            asdict(result),
            indent=4
        )
    )