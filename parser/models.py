from dataclasses import dataclass, field


@dataclass
class FileMetadata:
    path: str
    imports: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    function_calls: dict[
        str,
        list[str]
    ] = field(
        default_factory=dict
    )

    defined_functions: dict[str, str] = field(
        default_factory=dict
    )


@dataclass
class RepositoryMetadata:
    files: dict[str, FileMetadata] = field(
        default_factory=dict
    )