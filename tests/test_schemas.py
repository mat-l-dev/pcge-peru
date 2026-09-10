import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"
DATA_2019_DIR = REPO_ROOT / "src" / "pcge" / "data" / "2019"
DATA_2026_DIR = REPO_ROOT / "src" / "pcge" / "data" / "2026"


@pytest.fixture(scope="module")
def entries_schema() -> dict:
    schema_path = SCHEMAS_DIR / "entries.schema.json"
    with schema_path.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def metadata_schema() -> dict:
    schema_path = SCHEMAS_DIR / "metadata.schema.json"
    with schema_path.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def entries_validator(entries_schema: dict) -> Draft202012Validator:
    return Draft202012Validator(entries_schema)


@pytest.fixture(scope="module")
def metadata_validator(metadata_schema: dict) -> Draft202012Validator:
    return Draft202012Validator(metadata_schema)


def test_entries_schema_is_valid_draft_2020_12(entries_schema: dict):
    Draft202012Validator.check_schema(entries_schema)


def test_metadata_schema_is_valid_draft_2020_12(metadata_schema: dict):
    Draft202012Validator.check_schema(metadata_schema)


def test_packaged_entries_2026_conforms_to_schema(
    entries_validator: Draft202012Validator,
):
    entries_path = DATA_2026_DIR / "entries.json"
    with entries_path.open(encoding="utf-8") as f:
        entries_data = json.load(f)

    assert isinstance(entries_data, list)
    assert len(entries_data) == 1636
    entries_validator.validate(entries_data)


def test_packaged_metadata_2026_conforms_to_schema(
    metadata_validator: Draft202012Validator,
):
    metadata_path = DATA_2026_DIR / "metadata.json"
    with metadata_path.open(encoding="utf-8") as f:
        metadata_data = json.load(f)

    assert isinstance(metadata_data, dict)
    metadata_validator.validate(metadata_data)


def test_packaged_entries_2019_conforms_to_schema(
    entries_validator: Draft202012Validator,
):
    entries_path = DATA_2019_DIR / "entries.json"
    with entries_path.open(encoding="utf-8") as f:
        entries_data = json.load(f)

    assert isinstance(entries_data, list)
    assert len(entries_data) == 1757
    entries_validator.validate(entries_data)


def test_packaged_metadata_2019_conforms_to_schema(
    metadata_validator: Draft202012Validator,
):
    metadata_path = DATA_2019_DIR / "metadata.json"
    with metadata_path.open(encoding="utf-8") as f:
        metadata_data = json.load(f)

    assert isinstance(metadata_data, dict)
    metadata_validator.validate(metadata_data)


@pytest.mark.parametrize(
    ("invalid_entry", "match_keyword"),
    [
        (
            {"code": "10A", "name": "Caja", "parent_code": "1"},
            "pattern",
        ),
        (
            {"code": "1234567", "name": "Siete dígitos", "parent_code": "123456"},
            "pattern",
        ),
        (
            {"code": "10", "name": "Caja", "parent_code": "123456"},
            "anyOf",
        ),
        (
            {"code": "10", "name": "Caja", "parent_code": 1},
            "anyOf",
        ),
        (
            {"code": "", "name": "Vacío", "parent_code": None},
            "pattern",
        ),
        (
            {"code": "10", "name": "", "parent_code": "1"},
            "minLength",
        ),
        (
            {"code": "10", "parent_code": "1"},
            "required",
        ),
        (
            {
                "code": "10",
                "name": "Caja",
                "parent_code": "1",
                "extra_field": "disallowed",
            },
            "additionalProperties",
        ),
    ],
)
def test_entries_schema_rejects_structural_violations(
    entries_validator: Draft202012Validator, invalid_entry: dict, match_keyword: str
):
    valid_root = {"code": "1", "name": "Activo", "parent_code": None}
    instance = [valid_root, invalid_entry]
    with pytest.raises(ValidationError) as exc_info:
        entries_validator.validate(instance)
    assert exc_info.value.validator == match_keyword


def test_entries_schema_rejects_non_array_root(
    entries_validator: Draft202012Validator,
):
    with pytest.raises(ValidationError) as exc_info:
        entries_validator.validate({"code": "1", "name": "Activo", "parent_code": None})
    assert exc_info.value.validator == "type"


@pytest.mark.parametrize(
    ("invalid_metadata", "match_keyword"),
    [
        (
            {
                "pcge_version": "2026",
                "schema_version": 2,
                "dataset_revision": 1,
                "entry_count": 1636,
            },
            "const",
        ),
        (
            {
                "pcge_version": "2026",
                "schema_version": 1,
                "dataset_revision": 0,
                "entry_count": 1636,
            },
            "minimum",
        ),
        (
            {
                "pcge_version": "2026",
                "schema_version": 1,
                "dataset_revision": 1,
                "entry_count": -1,
            },
            "minimum",
        ),
        (
            {
                "pcge_version": "2026-beta",
                "schema_version": 1,
                "dataset_revision": 1,
                "entry_count": 1636,
            },
            "pattern",
        ),
        (
            {
                "pcge_version": "2026",
                "dataset_revision": 1,
                "entry_count": 1636,
            },
            "required",
        ),
        (
            {
                "pcge_version": "2026",
                "schema_version": 1,
                "dataset_revision": 1,
                "entry_count": 1636,
                "extra": "value",
            },
            "additionalProperties",
        ),
    ],
)
def test_metadata_schema_rejects_structural_violations(
    metadata_validator: Draft202012Validator,
    invalid_metadata: dict,
    match_keyword: str,
):
    with pytest.raises(ValidationError) as exc_info:
        metadata_validator.validate(invalid_metadata)
    assert exc_info.value.validator == match_keyword


def test_metadata_schema_rejects_non_object_root(
    metadata_validator: Draft202012Validator,
):
    with pytest.raises(ValidationError) as exc_info:
        metadata_validator.validate(["not", "an", "object"])
    assert exc_info.value.validator == "type"


def test_runtime_does_not_import_jsonschema():
    cmd = [
        sys.executable,
        "-c",
        (
            "import sys, pcge; "
            "assert 'jsonschema' not in sys.modules, "
            "'jsonschema leaked into runtime'"
        ),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert res.returncode == 0
