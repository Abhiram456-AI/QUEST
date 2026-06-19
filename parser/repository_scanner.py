from pathlib import Path


class RepositoryScanner:
    EXCLUDED_DIRS = {
    "venv",
    ".venv",
    ".git",
    "__pycache__",
    "node_modules",
    "site-packages",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".tox"
}
    EXCLUDED_EXTENSIONS = {
    ".pyc",
    ".so",
    ".dll",
    ".dylib"
}

    def __init__(self, repository_path: str):
        self.repository_path = Path(repository_path)

    def discover_python_files(self):
        python_files = []

        for file_path in self.repository_path.rglob("*.py"):

            if any(
                part in self.EXCLUDED_DIRS
                for part in file_path.parts
            ):
                continue

            python_files.append(file_path)

        return python_files