import pcge
from pcge import (
    PCGECatalog,
    PCGEDataError,
    PCGEEntry,
    PCGELevel,
    PCGEMetadata,
    load_catalog,
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
    assert not hasattr(pcge, "validate_dataset")
    assert len(pcge.__all__) == 6
    assert pcge.__all__ == [
        "PCGECatalog",
        "PCGEDataError",
        "PCGEEntry",
        "PCGELevel",
        "PCGEMetadata",
        "load_catalog",
    ]
