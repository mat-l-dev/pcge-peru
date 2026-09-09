import pytest

from pcge.exceptions import PCGEDataError
from pcge.metadata import PCGEMetadata
from pcge.models import PCGEEntry
from pcge.validation import validate_dataset


@pytest.fixture
def synthetic_hierarchy_1_to_6() -> list[PCGEEntry]:
    # Synthetic fixture for testing 1-6 digits hierarchy
    return [
        PCGEEntry(code="6", name="Sintético Elemento 6", parent_code=None),
        PCGEEntry(code="65", name="Sintético Cuenta 65", parent_code="6"),
        PCGEEntry(code="655", name="Sintético Subcuenta 655", parent_code="65"),
        PCGEEntry(code="6551", name="Sintético Divisionaria 6551", parent_code="655"),
        PCGEEntry(
            code="65511",
            name="Sintético Sub-divisionaria 65511",
            parent_code="6551",
        ),
        PCGEEntry(
            code="655111",
            name="Sintético Registro 6 Dígitos 655111",
            parent_code="65511",
        ),
    ]


def test_validate_dataset_valid(synthetic_hierarchy_1_to_6: list[PCGEEntry]):
    meta = PCGEMetadata(
        pcge_version="2026",
        schema_version=1,
        dataset_revision=1,
        entry_count=len(synthetic_hierarchy_1_to_6),
    )
    result = validate_dataset(synthetic_hierarchy_1_to_6, meta)
    assert isinstance(result, tuple)
    assert len(result) == len(synthetic_hierarchy_1_to_6)
    assert result == tuple(synthetic_hierarchy_1_to_6)

    for original, returned in zip(synthetic_hierarchy_1_to_6, result, strict=True):
        assert original is returned


def test_validate_dataset_generator_consumed_once(
    synthetic_hierarchy_1_to_6: list[PCGEEntry],
):
    consumed_count = 0

    def gen():
        nonlocal consumed_count
        for item in synthetic_hierarchy_1_to_6:
            consumed_count += 1
            yield item

    meta = PCGEMetadata(
        pcge_version="2026",
        schema_version=1,
        dataset_revision=1,
        entry_count=len(synthetic_hierarchy_1_to_6),
    )
    result = validate_dataset(gen(), meta)
    assert len(result) == len(synthetic_hierarchy_1_to_6)
    assert consumed_count == len(synthetic_hierarchy_1_to_6)


def test_validate_dataset_invalid_metadata_type(
    synthetic_hierarchy_1_to_6: list[PCGEEntry],
):
    with pytest.raises(TypeError):
        validate_dataset(synthetic_hierarchy_1_to_6, "not_metadata")  # type: ignore[arg-type]


def test_validate_dataset_unsupported_schema_version(
    synthetic_hierarchy_1_to_6: list[PCGEEntry],
):
    meta = PCGEMetadata(
        pcge_version="2026",
        schema_version=2,
        dataset_revision=1,
        entry_count=len(synthetic_hierarchy_1_to_6),
    )
    with pytest.raises(PCGEDataError, match="Unsupported schema_version"):
        validate_dataset(synthetic_hierarchy_1_to_6, meta)


def test_validate_dataset_incorrect_entry_count(
    synthetic_hierarchy_1_to_6: list[PCGEEntry],
):
    meta = PCGEMetadata(
        pcge_version="2026",
        schema_version=1,
        dataset_revision=1,
        entry_count=999,
    )
    with pytest.raises(PCGEDataError, match="entry count"):
        validate_dataset(synthetic_hierarchy_1_to_6, meta)


def test_validate_dataset_code_with_more_than_six_digits():
    e1 = PCGEEntry(code="6", name="Elemento", parent_code=None)
    e7 = PCGEEntry(code="6551111", name="Sintético 7 dígitos", parent_code="6")
    meta = PCGEMetadata(
        pcge_version="2026",
        schema_version=1,
        dataset_revision=1,
        entry_count=2,
    )
    with pytest.raises(PCGEDataError, match="invalid code length"):
        validate_dataset([e1, e7], meta)


def test_validate_dataset_duplicate_code():
    e1 = PCGEEntry(code="1", name="Activo", parent_code=None)
    e1_dup = PCGEEntry(code="1", name="Activo duplicado", parent_code=None)
    meta = PCGEMetadata(
        pcge_version="2026",
        schema_version=1,
        dataset_revision=1,
        entry_count=2,
    )
    with pytest.raises(PCGEDataError) as exc_info:
        validate_dataset([e1, e1_dup], meta)
    assert exc_info.value.__cause__ is not None


def test_validate_dataset_missing_parent():
    e10 = PCGEEntry(code="10", name="Cuenta sin padre", parent_code="1")
    meta = PCGEMetadata(
        pcge_version="2026",
        schema_version=1,
        dataset_revision=1,
        entry_count=1,
    )
    with pytest.raises(PCGEDataError) as exc_info:
        validate_dataset([e10], meta)
    assert exc_info.value.__cause__ is not None


def test_validate_dataset_cycle():
    e10 = PCGEEntry(code="10", name="A", parent_code="20")
    e20 = PCGEEntry(code="20", name="B", parent_code="10")
    meta = PCGEMetadata(
        pcge_version="2026",
        schema_version=1,
        dataset_revision=1,
        entry_count=2,
    )
    with pytest.raises(PCGEDataError) as exc_info:
        validate_dataset([e10, e20], meta)
    assert exc_info.value.__cause__ is not None


def test_validate_dataset_parent_not_matching_prefix():
    root9 = PCGEEntry(code="9", name="Raíz 9", parent_code=None)
    child10 = PCGEEntry(code="10", name="Hijo 10 con padre 9", parent_code="9")
    meta = PCGEMetadata(
        pcge_version="2026",
        schema_version=1,
        dataset_revision=1,
        entry_count=2,
    )
    with pytest.raises(PCGEDataError, match="expected prefix"):
        validate_dataset([root9, child10], meta)


def test_validate_dataset_six_digit_official_code_without_sixth_pcge_level(
    synthetic_hierarchy_1_to_6: list[PCGEEntry],
):
    entry_6 = synthetic_hierarchy_1_to_6[-1]
    assert entry_6.code_length == 6
    assert entry_6.pcge_level is None

    meta = PCGEMetadata(
        pcge_version="2026",
        schema_version=1,
        dataset_revision=1,
        entry_count=len(synthetic_hierarchy_1_to_6),
    )
    validated = validate_dataset(synthetic_hierarchy_1_to_6, meta)
    assert validated[-1].code == "655111"
    assert validated[-1].code_length == 6
    assert validated[-1].pcge_level is None
