from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PCGEMetadata:
    pcge_version: str
    schema_version: int
    dataset_revision: int
    entry_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.pcge_version, str):
            raise TypeError("pcge_version must be a str")
        if not self.pcge_version:
            raise ValueError("pcge_version cannot be empty")
        if not (self.pcge_version.isascii() and self.pcge_version.isdigit()):
            raise ValueError("pcge_version must contain only ASCII digits 0-9")

        if isinstance(self.schema_version, bool) or not isinstance(
            self.schema_version, int
        ):
            raise TypeError("schema_version must be an int")
        if self.schema_version < 1:
            raise ValueError("schema_version must be >= 1")

        if isinstance(self.dataset_revision, bool) or not isinstance(
            self.dataset_revision, int
        ):
            raise TypeError("dataset_revision must be an int")
        if self.dataset_revision < 1:
            raise ValueError("dataset_revision must be >= 1")

        if isinstance(self.entry_count, bool) or not isinstance(self.entry_count, int):
            raise TypeError("entry_count must be an int")
        if self.entry_count < 0:
            raise ValueError("entry_count must be >= 0")
