import pcge
from pcge import (
    PCGECatalog,
    PCGEDataError,
    PCGEEntry,
    PCGELevel,
    PCGEMetadata,
    load_catalog,
    validate_dataset,
)


def test_package_can_be_imported():
    assert pcge is not None


def test_public_api_exports():
    assert pcge.PCGECatalog is PCGECatalog
    assert pcge.PCGEDataError is PCGEDataError
    assert pcge.PCGEEntry is PCGEEntry
    assert pcge.PCGELevel is PCGELevel
    assert pcge.PCGEMetadata is PCGEMetadata
    assert pcge.load_catalog is load_catalog
    assert pcge.validate_dataset is validate_dataset
    assert pcge.__all__ == [
        "PCGECatalog",
        "PCGEDataError",
        "PCGEEntry",
        "PCGELevel",
        "PCGEMetadata",
        "load_catalog",
        "validate_dataset",
    ]
