import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
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
def source_schema() -> dict:
    schema_path = SCHEMAS_DIR / "source.schema.json"
    with schema_path.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def anomalies_schema() -> dict:
    schema_path = SCHEMAS_DIR / "anomalies.schema.json"
    with schema_path.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def entries_validator(entries_schema: dict) -> Draft202012Validator:
    return Draft202012Validator(entries_schema, format_checker=FormatChecker())


@pytest.fixture(scope="module")
def metadata_validator(metadata_schema: dict) -> Draft202012Validator:
    return Draft202012Validator(metadata_schema, format_checker=FormatChecker())


@pytest.fixture(scope="module")
def source_validator(source_schema: dict) -> Draft202012Validator:
    return Draft202012Validator(source_schema, format_checker=FormatChecker())


@pytest.fixture(scope="module")
def anomalies_validator(anomalies_schema: dict) -> Draft202012Validator:
    return Draft202012Validator(anomalies_schema, format_checker=FormatChecker())


def test_entries_schema_is_valid_draft_2020_12(entries_schema: dict):
    Draft202012Validator.check_schema(entries_schema)


def test_metadata_schema_is_valid_draft_2020_12(metadata_schema: dict):
    Draft202012Validator.check_schema(metadata_schema)


def test_source_schema_is_valid_draft_2020_12(source_schema: dict):
    Draft202012Validator.check_schema(source_schema)


def test_anomalies_schema_is_valid_draft_2020_12(anomalies_schema: dict):
    Draft202012Validator.check_schema(anomalies_schema)


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


def test_packaged_source_2026_conforms_to_schema(
    source_validator: Draft202012Validator,
):
    source_path = DATA_2026_DIR / "source.json"
    with source_path.open(encoding="utf-8") as f:
        source_data = json.load(f)

    assert isinstance(source_data, dict)
    source_validator.validate(source_data)


def test_packaged_anomalies_2026_conforms_to_schema(
    anomalies_validator: Draft202012Validator,
):
    anomalies_path = DATA_2026_DIR / "anomalies.json"
    with anomalies_path.open(encoding="utf-8") as f:
        anomalies_data = json.load(f)

    assert isinstance(anomalies_data, list)
    assert len(anomalies_data) == 1
    anomalies_validator.validate(anomalies_data)


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


def test_packaged_source_2019_conforms_to_schema(
    source_validator: Draft202012Validator,
):
    source_path = DATA_2019_DIR / "source.json"
    with source_path.open(encoding="utf-8") as f:
        source_data = json.load(f)

    assert isinstance(source_data, dict)
    source_validator.validate(source_data)


def test_packaged_anomalies_2019_conforms_to_schema(
    anomalies_validator: Draft202012Validator,
):
    anomalies_path = DATA_2019_DIR / "anomalies.json"
    with anomalies_path.open(encoding="utf-8") as f:
        anomalies_data = json.load(f)

    assert isinstance(anomalies_data, list)
    assert len(anomalies_data) == 10
    anomalies_validator.validate(anomalies_data)


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


def test_source_schema_rejects_lowercase_hashes(
    source_validator: Draft202012Validator,
):
    source_path = DATA_2026_DIR / "source.json"
    with source_path.open(encoding="utf-8") as f:
        valid_source = json.load(f)

    invalid_source_1 = dict(valid_source)
    invalid_source_1["source_sha256"] = valid_source["source_sha256"].lower()
    with pytest.raises(ValidationError) as exc1:
        source_validator.validate(invalid_source_1)
    assert exc1.value.validator == "pattern"

    invalid_source_2 = dict(valid_source)
    invalid_source_2["dataset_sha256"] = valid_source["dataset_sha256"].lower()
    with pytest.raises(ValidationError) as exc2:
        source_validator.validate(invalid_source_2)
    assert exc2.value.validator == "pattern"


def test_source_schema_rejects_invalid_date_format(
    source_validator: Draft202012Validator,
):
    source_path = DATA_2026_DIR / "source.json"
    with source_path.open(encoding="utf-8") as f:
        valid_source = json.load(f)

    invalid_date = dict(valid_source)
    invalid_date["resolution_date"] = "2026/09/04"
    with pytest.raises(ValidationError) as exc:
        source_validator.validate(invalid_date)
    assert exc.value.validator == "pattern"


def test_anomalies_schema_rejects_invalid_occurrence(
    anomalies_validator: Draft202012Validator,
):
    anomalies_path = DATA_2026_DIR / "anomalies.json"
    with anomalies_path.open(encoding="utf-8") as f:
        valid_anomalies = json.load(f)

    invalid_anom = [dict(valid_anomalies[0])]
    invalid_occ = dict(invalid_anom[0]["occurrences"][0])
    del invalid_occ["printed_parent_code"]
    invalid_anom[0]["occurrences"] = [invalid_occ]
    with pytest.raises(ValidationError) as exc:
        anomalies_validator.validate(invalid_anom)
    assert exc.value.validator == "required"


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


@pytest.mark.parametrize("field", ["code", "parent_code"])
@pytest.mark.parametrize("suffix", ["\n", "\r\n", "\u2028"])
def test_entries_schema_rejects_trailing_line_breaks(
    entries_validator: Draft202012Validator, field: str, suffix: str
):
    from pcge import PCGEEntry

    entry = {"code": "10", "name": "Caja", "parent_code": "1"}
    entry[field] += suffix
    with pytest.raises(ValidationError):
        entries_validator.validate([entry])
    with pytest.raises(ValueError):
        PCGEEntry(**entry)


@pytest.mark.parametrize("name", ["   ", "\t\n", "\u00a0\u2003"])
def test_entries_schema_and_model_reject_whitespace_only_names(
    entries_validator: Draft202012Validator, name: str
):
    from pcge import PCGEEntry

    entry = {"code": "10", "name": name, "parent_code": "1"}
    with pytest.raises(ValidationError, match="does not match"):
        entries_validator.validate([entry])
    with pytest.raises(ValueError, match="whitespace only"):
        PCGEEntry(**entry)


def test_metadata_schema_rejects_trailing_newline(
    metadata_validator: Draft202012Validator,
):
    metadata = json.loads((DATA_2026_DIR / "metadata.json").read_text(encoding="utf-8"))
    metadata["pcge_version"] += "\n"
    with pytest.raises(ValidationError) as exc:
        metadata_validator.validate(metadata)
    assert exc.value.validator == "pattern"


@pytest.mark.parametrize(
    "field",
    [
        "resolution_date",
        "publication_date",
        "mandatory_effective_date",
        "source_sha256",
        "dataset_sha256",
    ],
)
def test_source_schema_rejects_trailing_newline(
    source_validator: Draft202012Validator, field: str
):
    source = json.loads((DATA_2026_DIR / "source.json").read_text(encoding="utf-8"))
    source[field] += "\n"
    with pytest.raises(ValidationError) as exc:
        source_validator.validate(source)
    assert exc.value.validator == "pattern"


@pytest.mark.parametrize(
    "field", ["resolution_date", "publication_date", "mandatory_effective_date"]
)
@pytest.mark.parametrize("value", ["2026-02-30", "2026-13-01", "2023-02-29"])
def test_source_schema_rejects_impossible_calendar_dates(
    source_validator: Draft202012Validator, field: str, value: str
):
    source = json.loads((DATA_2026_DIR / "source.json").read_text(encoding="utf-8"))
    source[field] = value
    with pytest.raises(ValidationError) as exc:
        source_validator.validate(source)
    assert exc.value.validator == "format"


def test_source_schema_accepts_real_leap_day(source_validator: Draft202012Validator):
    source = json.loads((DATA_2026_DIR / "source.json").read_text(encoding="utf-8"))
    source["resolution_date"] = "2024-02-29"
    source_validator.validate(source)


@pytest.mark.parametrize(
    "field",
    [
        "title",
        "authority",
        "resolution",
        "resolution_url",
        "source_filename",
        "catalog_chapter",
    ],
)
def test_source_schema_rejects_whitespace_only_strings(
    source_validator: Draft202012Validator, field: str
):
    source = json.loads((DATA_2026_DIR / "source.json").read_text(encoding="utf-8"))
    source[field] = " \t\n\u00a0"
    with pytest.raises(ValidationError) as exc:
        source_validator.validate(source)
    assert exc.value.validator == "pattern"


@pytest.mark.parametrize(
    "field", ["code", "codes", "printed_code", "printed_parent_code"]
)
@pytest.mark.parametrize("value", [" 70992", "70992 ", "70992\n"])
def test_anomalies_schema_rejects_surrounding_whitespace_in_codes(
    anomalies_validator: Draft202012Validator, field: str, value: str
):
    anomalies = json.loads(
        (DATA_2026_DIR / "anomalies.json").read_text(encoding="utf-8")
    )
    anomaly = anomalies[0]
    if field in ("code", "codes"):
        anomaly.pop("code", None)
        anomaly.pop("codes", None)
        anomaly[field] = [value] if field == "codes" else value
    else:
        anomaly["occurrences"][0][field] = value
    with pytest.raises(ValidationError) as exc:
        anomalies_validator.validate(anomalies)
    assert exc.value.validator == "pattern"


@pytest.mark.parametrize(
    "field",
    [
        "id",
        "type",
        "status",
        "description",
        "decision",
        "confirmation_no_invented_code",
        "printed_name",
        "disposition",
    ],
)
def test_anomalies_schema_rejects_whitespace_only_strings(
    anomalies_validator: Draft202012Validator, field: str
):
    anomalies = json.loads(
        (DATA_2026_DIR / "anomalies.json").read_text(encoding="utf-8")
    )
    if field in ("printed_name", "disposition"):
        anomalies[0]["occurrences"][0][field] = " \t\n\u00a0"
    else:
        anomalies[0][field] = " \t\n\u00a0"
    with pytest.raises(ValidationError) as exc:
        anomalies_validator.validate(anomalies)
    assert exc.value.validator == "pattern"


@pytest.mark.parametrize("field", ["code", "codes"])
def test_anomalies_schema_preserves_non_numeric_codes_and_documentary_text(
    anomalies_validator: Draft202012Validator, field: str
):
    anomalies = json.loads(
        (DATA_2026_DIR / "anomalies.json").read_text(encoding="utf-8")
    )
    anomaly = anomalies[0]
    anomaly.pop("code", None)
    anomaly.pop("codes", None)
    anomaly[field] = ["ERR-63432"] if field == "codes" else "ERR-63432"
    anomaly["occurrences"][0]["printed_code"] = "ERR-63432"
    anomaly["occurrences"][0]["printed_parent_code"] = "Sin código"
    anomaly["occurrences"][0]["printed_name"] = "  Nombre documental \n"
    anomalies_validator.validate(anomalies)
