import pcge
from pcge import (
    PCGEAnomaly,
    PCGEAnomalyOccurrence,
    PCGECatalog,
    PCGEDataError,
    PCGEEntry,
    PCGELevel,
    PCGEMetadata,
    PCGEProvenance,
    available_versions,
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
    assert pcge.PCGEProvenance is PCGEProvenance
    assert pcge.PCGEAnomaly is PCGEAnomaly
    assert pcge.PCGEAnomalyOccurrence is PCGEAnomalyOccurrence
    assert pcge.available_versions is available_versions
    assert pcge.load_catalog is load_catalog
    assert not hasattr(pcge, "validate_dataset")
    assert len(pcge.__all__) == 10
    assert pcge.__all__ == [
        "PCGECatalog",
        "PCGEDataError",
        "PCGEEntry",
        "PCGELevel",
        "PCGEMetadata",
        "PCGEProvenance",
        "PCGEAnomaly",
        "PCGEAnomalyOccurrence",
        "available_versions",
        "load_catalog",
    ]
