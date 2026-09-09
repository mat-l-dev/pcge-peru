import pcge
from pcge import PCGECatalog, PCGEEntry, PCGELevel


def test_package_can_be_imported():
    assert pcge is not None


def test_public_api_exports():
    assert pcge.PCGECatalog is PCGECatalog
    assert pcge.PCGEEntry is PCGEEntry
    assert pcge.PCGELevel is PCGELevel
    assert pcge.__all__ == ["PCGECatalog", "PCGEEntry", "PCGELevel"]
