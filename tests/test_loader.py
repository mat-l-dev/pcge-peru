import json

import pytest

from pcge.exceptions import PCGEDataError
from pcge.loader import load_catalog


def test_load_catalog_valid_simulated_resources(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()

    meta_json = {
        "pcge_version": "2026",
        "schema_version": 1,
        "dataset_revision": 1,
        "entry_count": 2,
    }
    entries_json = [
        {"code": "1", "name": "Activo", "parent_code": None},
        {"code": "10", "name": "Efectivo", "parent_code": "1"},
    ]

    (version_dir / "metadata.json").write_text(json.dumps(meta_json), encoding="utf-8")
    (version_dir / "entries.json").write_text(
        json.dumps(entries_json), encoding="utf-8"
    )

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    cat = load_catalog("2026")
    assert len(cat) == 2
    assert [e.code for e in cat] == ["1", "10"]
    assert cat.metadata is not None
    assert cat.metadata.pcge_version == "2026"
    assert cat.metadata.entry_count == 2


def test_load_catalog_default_version(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()

    meta_json = {
        "pcge_version": "2026",
        "schema_version": 1,
        "dataset_revision": 1,
        "entry_count": 1,
    }
    entries_json = [
        {"code": "1", "name": "Activo", "parent_code": None},
    ]

    (version_dir / "metadata.json").write_text(json.dumps(meta_json), encoding="utf-8")
    (version_dir / "entries.json").write_text(
        json.dumps(entries_json), encoding="utf-8"
    )

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    # Calling without arguments defaults to version 2026
    cat = load_catalog()
    assert len(cat) == 1
    assert cat["1"].name == "Activo"


def test_load_catalog_independent_of_working_directory(tmp_path, monkeypatch):
    version_dir = tmp_path / "resources" / "2026"
    version_dir.mkdir(parents=True)

    meta_json = {
        "pcge_version": "2026",
        "schema_version": 1,
        "dataset_revision": 1,
        "entry_count": 1,
    }
    entries_json = [
        {"code": "1", "name": "Activo", "parent_code": None},
    ]

    (version_dir / "metadata.json").write_text(json.dumps(meta_json), encoding="utf-8")
    (version_dir / "entries.json").write_text(
        json.dumps(entries_json), encoding="utf-8"
    )

    monkeypatch.setattr(
        "pcge.loader.importlib_resources.files",
        lambda pkg: tmp_path / "resources",
    )

    other_dir = tmp_path / "other_working_directory"
    other_dir.mkdir()
    monkeypatch.chdir(other_dir)

    cat = load_catalog("2026")
    assert len(cat) == 1


@pytest.mark.parametrize("invalid_type", [123, None, ("2026",), ["2026"]])
def test_load_catalog_invalid_version_type(invalid_type):
    with pytest.raises(TypeError):
        load_catalog(invalid_type)  # type: ignore[arg-type]


def test_load_catalog_empty_version():
    with pytest.raises(PCGEDataError, match="empty"):
        load_catalog("")


@pytest.mark.parametrize(
    "invalid_version",
    [
        "2026/1",
        "2026-v1",
        "2026.0",
        "2026\\data",
        "../2026",
        "2026 ",
        " 2026",
        "2026á",
    ],
)
def test_load_catalog_invalid_version_characters(invalid_version):
    with pytest.raises(PCGEDataError, match="ASCII digits"):
        load_catalog(invalid_version)


def test_load_catalog_unavailable_version():
    with pytest.raises(PCGEDataError, match="not available"):
        load_catalog("9999")


def test_load_catalog_real_2026_integration():
    cat = load_catalog("2026")
    assert len(cat) == 1636
    assert cat.metadata is not None
    assert cat.metadata.pcge_version == "2026"
    assert cat.metadata.schema_version == 1
    assert cat.metadata.dataset_revision == 1
    assert cat.metadata.entry_count == 1636

    # Default call without argument loads the same 2026 catalog
    cat_default = load_catalog()
    assert len(cat_default) == 1636
    assert cat_default.metadata == cat.metadata

    # Confirm tuple(catalog) preserves documentary order
    import importlib.resources as importlib_resources

    data_pkg = importlib_resources.files("pcge.data")
    entries_text = data_pkg.joinpath("2026", "entries.json").read_text(encoding="utf-8")
    raw_entries = json.loads(entries_text)
    expected_codes = [item["code"] for item in raw_entries]
    catalog_codes = [entry.code for entry in cat]
    assert catalog_codes == expected_codes
    assert tuple(cat)[0].code == "1"
    assert tuple(cat)[-1].code == "93"


def test_load_catalog_missing_entries_file(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()
    (version_dir / "metadata.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="entries.json.*not found"):
        load_catalog("2026")


def test_load_catalog_missing_metadata_file(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()
    (version_dir / "entries.json").write_text("[]", encoding="utf-8")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="metadata.json.*not found"):
        load_catalog("2026")


def test_load_catalog_malformed_json(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()
    (version_dir / "metadata.json").write_text("{invalid_json", encoding="utf-8")
    (version_dir / "entries.json").write_text("[]", encoding="utf-8")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="Malformed JSON in 'metadata.json'"):
        load_catalog("2026")


def test_load_catalog_entries_malformed_json(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()
    meta_json = {
        "pcge_version": "2026",
        "schema_version": 1,
        "dataset_revision": 1,
        "entry_count": 0,
    }
    (version_dir / "metadata.json").write_text(json.dumps(meta_json), encoding="utf-8")
    (version_dir / "entries.json").write_text("[invalid_json", encoding="utf-8")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="Malformed JSON in 'entries.json'"):
        load_catalog("2026")


def test_load_catalog_metadata_duplicate_key(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()
    raw_metadata = """{
      "pcge_version": "2026",
      "schema_version": 1,
      "dataset_revision": 1,
      "entry_count": 1,
      "entry_count": 999
    }"""
    (version_dir / "metadata.json").write_text(raw_metadata, encoding="utf-8")
    (version_dir / "entries.json").write_text("[]", encoding="utf-8")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(
        PCGEDataError,
        match=(
            r"Duplicate JSON key 'entry_count' in 'metadata\.json' "
            r"for version '2026'"
        ),
    ):
        load_catalog("2026")


def test_load_catalog_entries_duplicate_key(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()
    meta_json = {
        "pcge_version": "2026",
        "schema_version": 1,
        "dataset_revision": 1,
        "entry_count": 1,
    }
    raw_entries = """[
      {
        "code": "1",
        "code": "9",
        "name": "Elemento",
        "parent_code": null
      }
    ]"""
    (version_dir / "metadata.json").write_text(json.dumps(meta_json), encoding="utf-8")
    (version_dir / "entries.json").write_text(raw_entries, encoding="utf-8")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(
        PCGEDataError,
        match=r"Duplicate JSON key 'code' in 'entries\.json' for version '2026'",
    ):
        load_catalog("2026")


def test_load_catalog_nested_object_duplicate_key(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()
    meta_json = {
        "pcge_version": "2026",
        "schema_version": 1,
        "dataset_revision": 1,
        "entry_count": 1,
    }
    raw_entries = """[
      {
        "code": "1",
        "name": "Elemento",
        "parent_code": null,
        "nested": {
          "tag": "a",
          "tag": "b"
        }
      }
    ]"""
    (version_dir / "metadata.json").write_text(json.dumps(meta_json), encoding="utf-8")
    (version_dir / "entries.json").write_text(raw_entries, encoding="utf-8")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(
        PCGEDataError,
        match=r"Duplicate JSON key 'tag' in 'entries\.json' for version '2026'",
    ):
        load_catalog("2026")


def test_load_catalog_metadata_not_object(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()
    (version_dir / "metadata.json").write_text("[1, 2, 3]", encoding="utf-8")
    (version_dir / "entries.json").write_text("[]", encoding="utf-8")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="must contain a JSON object"):
        load_catalog("2026")


def test_load_catalog_entries_not_array(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()
    meta_json = {
        "pcge_version": "2026",
        "schema_version": 1,
        "dataset_revision": 1,
        "entry_count": 0,
    }
    (version_dir / "metadata.json").write_text(json.dumps(meta_json), encoding="utf-8")
    (version_dir / "entries.json").write_text('{"code": "1"}', encoding="utf-8")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="must contain a JSON array"):
        load_catalog("2026")


def test_load_catalog_metadata_missing_keys(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()
    # Missing entry_count
    meta_json = {
        "pcge_version": "2026",
        "schema_version": 1,
        "dataset_revision": 1,
    }
    (version_dir / "metadata.json").write_text(json.dumps(meta_json), encoding="utf-8")
    (version_dir / "entries.json").write_text("[]", encoding="utf-8")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="missing required keys.*entry_count"):
        load_catalog("2026")


def test_load_catalog_metadata_extra_keys(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()
    meta_json = {
        "pcge_version": "2026",
        "schema_version": 1,
        "dataset_revision": 1,
        "entry_count": 0,
        "unexpected_extra": "foo",
    }
    (version_dir / "metadata.json").write_text(json.dumps(meta_json), encoding="utf-8")
    (version_dir / "entries.json").write_text("[]", encoding="utf-8")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="unexpected extra keys"):
        load_catalog("2026")


def test_load_catalog_metadata_bool_for_integer(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()
    meta_json = {
        "pcge_version": "2026",
        "schema_version": True,
        "dataset_revision": 1,
        "entry_count": 0,
    }
    (version_dir / "metadata.json").write_text(json.dumps(meta_json), encoding="utf-8")
    (version_dir / "entries.json").write_text("[]", encoding="utf-8")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="must be an integer, got bool"):
        load_catalog("2026")


def test_load_catalog_entries_element_not_object(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()
    meta_json = {
        "pcge_version": "2026",
        "schema_version": 1,
        "dataset_revision": 1,
        "entry_count": 2,
    }
    entries_json = [
        {"code": "1", "name": "Activo", "parent_code": None},
        "not_an_object",
    ]
    (version_dir / "metadata.json").write_text(json.dumps(meta_json), encoding="utf-8")
    (version_dir / "entries.json").write_text(
        json.dumps(entries_json), encoding="utf-8"
    )

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="index 1.*must be a JSON object"):
        load_catalog("2026")


def test_load_catalog_entries_missing_key_includes_index(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()
    meta_json = {
        "pcge_version": "2026",
        "schema_version": 1,
        "dataset_revision": 1,
        "entry_count": 2,
    }
    entries_json = [
        {"code": "1", "name": "Activo", "parent_code": None},
        {"code": "10", "name": "Efectivo"},  # missing parent_code
    ]
    (version_dir / "metadata.json").write_text(json.dumps(meta_json), encoding="utf-8")
    (version_dir / "entries.json").write_text(
        json.dumps(entries_json), encoding="utf-8"
    )

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(
        PCGEDataError, match="at index 1 missing keys: \\['parent_code'\\]"
    ):
        load_catalog("2026")


def test_load_catalog_version_mismatch(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()
    meta_json = {
        "pcge_version": "2025",  # Mismatch with requested 2026
        "schema_version": 1,
        "dataset_revision": 1,
        "entry_count": 0,
    }
    (version_dir / "metadata.json").write_text(json.dumps(meta_json), encoding="utf-8")
    (version_dir / "entries.json").write_text("[]", encoding="utf-8")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="does not match requested version"):
        load_catalog("2026")


def test_load_catalog_semantic_error_propagated_as_pcge_data_error(
    tmp_path, monkeypatch
):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()
    meta_json = {
        "pcge_version": "2026",
        "schema_version": 1,
        "dataset_revision": 1,
        "entry_count": 2,
    }
    entries_json = [
        {"code": "1", "name": "Activo", "parent_code": None},
        {"code": "20", "name": "Mercaderías", "parent_code": "1"},  # Prefix mismatch!
    ]
    (version_dir / "metadata.json").write_text(json.dumps(meta_json), encoding="utf-8")
    (version_dir / "entries.json").write_text(
        json.dumps(entries_json), encoding="utf-8"
    )

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="expected prefix"):
        load_catalog("2026")


def test_load_catalog_unsupported_schema_version(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()
    meta_json = {
        "pcge_version": "2026",
        "schema_version": 2,
        "dataset_revision": 1,
        "entry_count": 1,
    }
    entries_json = [
        {"code": "1", "name": "Activo", "parent_code": None},
    ]
    (version_dir / "metadata.json").write_text(json.dumps(meta_json), encoding="utf-8")
    (version_dir / "entries.json").write_text(
        json.dumps(entries_json), encoding="utf-8"
    )

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="Unsupported schema_version"):
        load_catalog("2026")


def test_load_catalog_code_with_more_than_six_digits(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()
    meta_json = {
        "pcge_version": "2026",
        "schema_version": 1,
        "dataset_revision": 1,
        "entry_count": 2,
    }
    entries_json = [
        {"code": "6", "name": "Elemento", "parent_code": None},
        {"code": "6551111", "name": "Sintético 7 dígitos", "parent_code": "655111"},
    ]
    (version_dir / "metadata.json").write_text(json.dumps(meta_json), encoding="utf-8")
    (version_dir / "entries.json").write_text(
        json.dumps(entries_json), encoding="utf-8"
    )

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="Invalid code length"):
        load_catalog("2026")


def test_load_catalog_duplicate_code_wrapped_in_data_error(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()
    meta_json = {
        "pcge_version": "2026",
        "schema_version": 1,
        "dataset_revision": 1,
        "entry_count": 2,
    }
    entries_json = [
        {"code": "1", "name": "Activo", "parent_code": None},
        {"code": "1", "name": "Activo duplicado", "parent_code": None},
    ]
    (version_dir / "metadata.json").write_text(json.dumps(meta_json), encoding="utf-8")
    (version_dir / "entries.json").write_text(
        json.dumps(entries_json), encoding="utf-8"
    )

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="Duplicate code"):
        load_catalog("2026")


def test_load_catalog_entry_count_mismatch_wrapped_in_data_error(tmp_path, monkeypatch):
    version_dir = tmp_path / "2026"
    version_dir.mkdir()
    meta_json = {
        "pcge_version": "2026",
        "schema_version": 1,
        "dataset_revision": 1,
        "entry_count": 5,
    }
    entries_json = [
        {"code": "1", "name": "Activo", "parent_code": None},
    ]
    (version_dir / "metadata.json").write_text(json.dumps(meta_json), encoding="utf-8")
    (version_dir / "entries.json").write_text(
        json.dumps(entries_json), encoding="utf-8"
    )

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="metadata.entry_count"):
        load_catalog("2026")
