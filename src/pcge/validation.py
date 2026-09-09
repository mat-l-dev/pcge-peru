from collections.abc import Iterable

from pcge.catalog import PCGECatalog
from pcge.exceptions import PCGEDataError
from pcge.metadata import PCGEMetadata
from pcge.models import PCGEEntry


def validate_dataset(
    entries: Iterable[PCGEEntry],
    metadata: PCGEMetadata,
) -> tuple[PCGEEntry, ...]:
    if not isinstance(metadata, PCGEMetadata):
        item_type = type(metadata).__name__
        raise TypeError(f"metadata must be PCGEMetadata, got {item_type}")

    if metadata.schema_version != 1:
        raise PCGEDataError(
            f"Unsupported schema_version: {metadata.schema_version}, expected 1"
        )

    entries_tuple = tuple(entries)

    for idx, entry in enumerate(entries_tuple):
        if not isinstance(entry, PCGEEntry):
            item_type = type(entry).__name__
            raise TypeError(
                f"All elements must be PCGEEntry, got {item_type} at index {idx}"
            )
        if entry.code_length < 1 or entry.code_length > 6:
            raise PCGEDataError(
                f"Entry at index {idx} has invalid code length {entry.code_length} "
                f"for code '{entry.code}'"
            )

    try:
        PCGECatalog(entries_tuple, metadata=metadata)
    except ValueError as err:
        raise PCGEDataError(f"Dataset integrity validation failed: {err}") from err

    for entry in entries_tuple:
        if entry.code_length > 1 and entry.parent_code != entry.code[:-1]:
            raise PCGEDataError(
                f"Canonical dataset entry '{entry.code}' has parent_code "
                f"'{entry.parent_code}', expected prefix '{entry.code[:-1]}'"
            )

    return entries_tuple
