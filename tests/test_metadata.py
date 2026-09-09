import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from pcge.metadata import PCGEMetadata


def test_metadata_valid_construction():
    meta = PCGEMetadata(
        pcge_version="2026",
        schema_version=1,
        dataset_revision=1,
        entry_count=100,
    )
    assert meta.pcge_version == "2026"
    assert meta.schema_version == 1
    assert meta.dataset_revision == 1
    assert meta.entry_count == 100


def test_metadata_is_immutable():
    meta = PCGEMetadata(
        pcge_version="2026",
        schema_version=1,
        dataset_revision=1,
        entry_count=100,
    )
    with pytest.raises(FrozenInstanceError):
        meta.pcge_version = "2027"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        meta.entry_count = 200  # type: ignore[misc]


def test_metadata_has_slots_and_no_dict():
    meta = PCGEMetadata(
        pcge_version="2026",
        schema_version=1,
        dataset_revision=1,
        entry_count=100,
    )
    assert not hasattr(meta, "__dict__")
    assert hasattr(meta, "__slots__")
    assert tuple(PCGEMetadata.__slots__) == (
        "pcge_version",
        "schema_version",
        "dataset_revision",
        "entry_count",
    )


def test_metadata_equality_by_value():
    m1 = PCGEMetadata(
        pcge_version="2026",
        schema_version=1,
        dataset_revision=1,
        entry_count=100,
    )
    m2 = PCGEMetadata(
        pcge_version="2026",
        schema_version=1,
        dataset_revision=1,
        entry_count=100,
    )
    assert m1 == m2
    assert hash(m1) == hash(m2)
    assert len({m1, m2}) == 1


@pytest.mark.parametrize("invalid_version", [123, None, ("2026",), ["2026"]])
def test_metadata_invalid_pcge_version_type(invalid_version):
    with pytest.raises(TypeError):
        PCGEMetadata(
            pcge_version=invalid_version,  # type: ignore[arg-type]
            schema_version=1,
            dataset_revision=1,
            entry_count=10,
        )


@pytest.mark.parametrize(
    "invalid_int_field", ["schema_version", "dataset_revision", "entry_count"]
)
@pytest.mark.parametrize("invalid_val", ["1", 1.5, None, [1]])
def test_metadata_invalid_integer_types(invalid_int_field, invalid_val):
    kwargs = {
        "pcge_version": "2026",
        "schema_version": 1,
        "dataset_revision": 1,
        "entry_count": 10,
    }
    kwargs[invalid_int_field] = invalid_val
    with pytest.raises(TypeError):
        PCGEMetadata(**kwargs)


@pytest.mark.parametrize(
    "int_field", ["schema_version", "dataset_revision", "entry_count"]
)
@pytest.mark.parametrize("bool_val", [True, False])
def test_metadata_rejects_bool_for_integer_fields(int_field, bool_val):
    kwargs = {
        "pcge_version": "2026",
        "schema_version": 1,
        "dataset_revision": 1,
        "entry_count": 10,
    }
    kwargs[int_field] = bool_val
    with pytest.raises(TypeError):
        PCGEMetadata(**kwargs)


@pytest.mark.parametrize("empty_or_invalid_version", ["", "2026-v1", "2026a", " 2026 "])
def test_metadata_empty_or_invalid_pcge_version(empty_or_invalid_version):
    with pytest.raises(ValueError):
        PCGEMetadata(
            pcge_version=empty_or_invalid_version,
            schema_version=1,
            dataset_revision=1,
            entry_count=10,
        )


def test_metadata_out_of_range_integers():
    # schema_version < 1
    with pytest.raises(ValueError):
        PCGEMetadata(
            pcge_version="2026",
            schema_version=0,
            dataset_revision=1,
            entry_count=10,
        )
    # dataset_revision < 1
    with pytest.raises(ValueError):
        PCGEMetadata(
            pcge_version="2026",
            schema_version=1,
            dataset_revision=0,
            entry_count=10,
        )
    # entry_count < 0
    with pytest.raises(ValueError):
        PCGEMetadata(
            pcge_version="2026",
            schema_version=1,
            dataset_revision=1,
            entry_count=-1,
        )


def test_json_schemas_validity():
    schemas_dir = Path(__file__).resolve().parent.parent / "schemas"
    entries_schema_path = schemas_dir / "entries.schema.json"
    metadata_schema_path = schemas_dir / "metadata.schema.json"

    assert entries_schema_path.exists()
    assert metadata_schema_path.exists()

    with entries_schema_path.open(encoding="utf-8") as f:
        entries_schema = json.load(f)

    with metadata_schema_path.open(encoding="utf-8") as f:
        metadata_schema = json.load(f)

    assert entries_schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert metadata_schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    assert entries_schema["type"] == "array"
    assert entries_schema["items"]["required"] == ["code", "name", "parent_code"]
    assert entries_schema["items"]["additionalProperties"] is False

    assert metadata_schema["type"] == "object"
    assert metadata_schema["required"] == [
        "pcge_version",
        "schema_version",
        "dataset_revision",
        "entry_count",
    ]
    assert metadata_schema["additionalProperties"] is False
