import hashlib
import importlib.resources as importlib_resources
import inspect
import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from pcge.exceptions import PCGEDataError
from pcge.loader import available_versions, load_catalog
from pcge.provenance import PCGEProvenance


def _create_simulated_snapshot(
    base_dir: Path,
    version: str = "2026",
    *,
    metadata: dict[str, Any] | str | None = None,
    entries: list[dict[str, Any]] | str | None = None,
    source: dict[str, Any] | str | None = None,
    anomalies: list[dict[str, Any]] | str | None = None,
    write_metadata: bool = True,
    write_entries: bool = True,
    write_source: bool = True,
    write_anomalies: bool = True,
) -> Path:
    version_dir = base_dir / version
    version_dir.mkdir(parents=True, exist_ok=True)

    entries_bytes = b""
    if write_entries:
        if entries is None:
            entries = [
                {"code": "1", "name": "Activo", "parent_code": None},
                {"code": "10", "name": "Efectivo", "parent_code": "1"},
            ]
        if isinstance(entries, str):
            entries_bytes = entries.encode("utf-8")
        else:
            entries_bytes = json.dumps(entries, indent=2).encode("utf-8")
        (version_dir / "entries.json").write_bytes(entries_bytes)

    if write_metadata:
        if metadata is None:
            metadata = {
                "pcge_version": version,
                "schema_version": 1,
                "dataset_revision": 1,
                "entry_count": 2,
            }
        if isinstance(metadata, str):
            (version_dir / "metadata.json").write_text(metadata, encoding="utf-8")
        else:
            (version_dir / "metadata.json").write_text(
                json.dumps(metadata, indent=2), encoding="utf-8"
            )

    if write_source:
        if source is None:
            calc_sha = hashlib.sha256(entries_bytes).hexdigest().upper()
            source = {
                "title": f"Plan Contable General Empresarial {version}",
                "authority": "Consejo Normativo de Contabilidad",
                "resolution": f"Resolución N.° 001-{version}-EF/30",
                "resolution_date": "2026-01-01",
                "publication_date": "2026-01-02",
                "mandatory_effective_date": "2026-01-03",
                "resolution_url": "https://example.com/resolution",
                "source_filename": f"PCGE_{version}.pdf",
                "source_sha256": "A" * 64,
                "dataset_sha256": calc_sha,
                "catalog_chapter": "Capítulo II",
                "catalog_pdf_pages": {"first": 1, "last": 10},
                "catalog_printed_pages": {"first": 1, "last": 10},
            }
        if isinstance(source, str):
            (version_dir / "source.json").write_text(source, encoding="utf-8")
        else:
            (version_dir / "source.json").write_text(
                json.dumps(source, indent=2), encoding="utf-8"
            )

    if write_anomalies:
        if anomalies is None:
            anomalies = []
        if isinstance(anomalies, str):
            (version_dir / "anomalies.json").write_text(anomalies, encoding="utf-8")
        else:
            (version_dir / "anomalies.json").write_text(
                json.dumps(anomalies, indent=2), encoding="utf-8"
            )

    return version_dir


def test_load_catalog_valid_simulated_resources(tmp_path, monkeypatch):
    _create_simulated_snapshot(tmp_path, "2026")
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    cat = load_catalog("2026")
    assert len(cat) == 2
    assert [e.code for e in cat] == ["1", "10"]
    assert cat.metadata is not None
    assert cat.metadata.pcge_version == "2026"
    assert cat.metadata.entry_count == 2
    assert cat.provenance is not None
    assert cat.anomalies == ()


def test_load_catalog_missing_version_raises_type_error():
    with pytest.raises(TypeError):
        load_catalog()  # type: ignore[call-arg]


def test_load_catalog_signature_has_no_default():
    signature = inspect.signature(load_catalog)
    assert signature.parameters["version"].default is inspect.Parameter.empty


def test_available_versions_returns_tuple():
    versions = available_versions()
    assert versions == ("2019", "2026")
    assert isinstance(versions, tuple)


def test_available_versions_independent_of_resources(monkeypatch):
    def fake_files(_):
        raise RuntimeError("Resources should not be accessed")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", fake_files)
    assert available_versions() == ("2019", "2026")


def test_load_catalog_independent_of_working_directory(tmp_path, monkeypatch):
    resources_dir = tmp_path / "resources"
    _create_simulated_snapshot(resources_dir, "2026")

    monkeypatch.setattr(
        "pcge.loader.importlib_resources.files",
        lambda pkg: resources_dir,
    )

    other_dir = tmp_path / "other_working_directory"
    other_dir.mkdir()
    monkeypatch.chdir(other_dir)

    cat = load_catalog("2026")
    assert len(cat) == 2


@pytest.mark.parametrize(
    "invalid_type",
    [123, None, ["2026"], ("2026",)],
)
def test_load_catalog_invalid_version_type(invalid_type):
    with pytest.raises(TypeError, match="version must be a str"):
        load_catalog(invalid_type)  # type: ignore[arg-type]


def test_load_catalog_empty_version():
    with pytest.raises(PCGEDataError, match="version cannot be empty"):
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
        "2026\u00e1",
    ],
)
def test_load_catalog_invalid_version_characters(invalid_version):
    with pytest.raises(PCGEDataError, match="only ASCII digits"):
        load_catalog(invalid_version)


def test_load_catalog_unavailable_version():
    with pytest.raises(PCGEDataError) as exc_info:
        load_catalog("9999")
    msg = str(exc_info.value)
    assert "9999" in msg
    assert "2019" in msg
    assert "2026" in msg


def test_load_catalog_unsupported_version_rejected_before_resource_access(
    monkeypatch,
):
    def fake_files(_):
        raise RuntimeError("Resources should not be accessed")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", fake_files)
    with pytest.raises(PCGEDataError, match="Version '9999' is not available"):
        load_catalog("9999")


def test_load_catalog_real_2019_integration():
    cat = load_catalog("2019")
    assert len(cat) == 1757
    assert cat.metadata is not None
    assert cat.metadata.pcge_version == "2019"
    assert cat.metadata.schema_version == 1
    assert cat.metadata.dataset_revision == 1
    assert cat.metadata.entry_count == 1757

    # Provenance
    prov = cat.provenance
    assert prov is not None
    assert isinstance(prov, PCGEProvenance)
    assert prov.title == "Plan Contable General Empresarial Modificado 2019"
    assert prov.authority == "Consejo Normativo de Contabilidad"
    assert prov.resolution == "Resolución N.° 002-2019-EF/30"
    assert prov.resolution_date == date(2019, 5, 16)
    assert prov.publication_date == date(2019, 5, 24)
    assert prov.mandatory_effective_date == date(2020, 1, 1)
    assert prov.source_filename == "PCGE_2019.pdf"
    assert (
        prov.source_sha256
        == "EC0CA9D36CD2F5CDB6D14ECB45A6E510879DF929372FDB033BC2DF88329EB9F2"
    )
    assert (
        prov.dataset_sha256
        == "FC70E43B94D0718373AB3B9F81202731E5295EDEDF0DF75231A2FFB3C2BEEC04"
    )
    assert prov.catalog_pdf_pages == (21, 62)
    assert prov.catalog_printed_pages == (20, 61)

    # Anomalies
    assert len(cat.anomalies) == 10


def test_load_catalog_real_2026_integration():
    cat = load_catalog("2026")
    assert len(cat) == 1636
    assert cat.metadata is not None
    assert cat.metadata.pcge_version == "2026"
    assert cat.metadata.schema_version == 1
    assert cat.metadata.dataset_revision == 1
    assert cat.metadata.entry_count == 1636

    # Provenance
    prov = cat.provenance
    assert prov is not None
    assert isinstance(prov, PCGEProvenance)
    assert prov.title == "Plan Contable General Empresarial 2026"
    assert prov.authority == "Consejo Normativo de Contabilidad"
    assert prov.resolution == "Resolución N.° 002-2026-EF/30"
    assert prov.resolution_date == date(2026, 9, 1)
    assert prov.publication_date == date(2026, 9, 4)
    assert prov.mandatory_effective_date == date(2028, 1, 1)
    assert (
        prov.source_filename
        == "8559148-plan-contable-general-empresarial-pcge-2026(2).pdf"
    )
    assert (
        prov.source_sha256
        == "48C568CA196C68348743DDA96C55C38593B0437CE732A4C5D77D7C9ACA896B19"
    )
    assert (
        prov.dataset_sha256
        == "70D6CB7DFC501A1306A0E934DF48409F70E83FFAE033676B49F297D9CBEAF43A"
    )
    assert prov.catalog_pdf_pages == (19, 52)
    assert prov.catalog_printed_pages == (17, 50)

    # Anomalies
    assert len(cat.anomalies) == 1

    # Documentary order
    data_pkg = importlib_resources.files("pcge.data")
    entries_bytes = data_pkg.joinpath("2026", "entries.json").read_bytes()
    raw_entries = json.loads(entries_bytes.decode("utf-8"))
    expected_codes = [item["code"] for item in raw_entries]
    catalog_codes = [entry.code for entry in cat]
    assert catalog_codes == expected_codes
    assert tuple(cat)[0].code == "1"
    assert tuple(cat)[-1].code == "93"


def test_independent_dataset_sha256_integrity():
    for version in available_versions():
        cat = load_catalog(version)
        data_pkg = importlib_resources.files("pcge.data")
        raw_bytes = data_pkg.joinpath(version, "entries.json").read_bytes()
        expected = hashlib.sha256(raw_bytes).hexdigest().upper()
        assert cat.provenance is not None
        assert cat.provenance.dataset_sha256 == expected


def test_load_catalog_missing_entries_file(tmp_path, monkeypatch):
    _create_simulated_snapshot(tmp_path, "2026", write_entries=False)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="entries.json.*not found"):
        load_catalog("2026")


def test_load_catalog_missing_metadata_file(tmp_path, monkeypatch):
    _create_simulated_snapshot(tmp_path, "2026", write_metadata=False)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="metadata.json.*not found"):
        load_catalog("2026")


def test_load_catalog_missing_source_file(tmp_path, monkeypatch):
    _create_simulated_snapshot(tmp_path, "2026", write_source=False)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="source.json.*not found"):
        load_catalog("2026")


def test_load_catalog_missing_anomalies_file(tmp_path, monkeypatch):
    _create_simulated_snapshot(tmp_path, "2026", write_anomalies=False)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="anomalies.json.*not found"):
        load_catalog("2026")


def test_load_catalog_malformed_json(tmp_path, monkeypatch):
    _create_simulated_snapshot(tmp_path, "2026", metadata="{invalid_json")
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="Malformed JSON in 'metadata.json'"):
        load_catalog("2026")


def test_load_catalog_entries_malformed_json(tmp_path, monkeypatch):
    _create_simulated_snapshot(
        tmp_path,
        "2026",
        entries="[invalid_json",
        metadata={
            "pcge_version": "2026",
            "schema_version": 1,
            "dataset_revision": 1,
            "entry_count": 0,
        },
    )
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="Malformed JSON in 'entries.json'"):
        load_catalog("2026")


def test_load_catalog_source_malformed_json(tmp_path, monkeypatch):
    _create_simulated_snapshot(tmp_path, "2026", source="{invalid_json")
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="Malformed JSON in 'source.json'"):
        load_catalog("2026")


def test_load_catalog_anomalies_malformed_json(tmp_path, monkeypatch):
    _create_simulated_snapshot(tmp_path, "2026", anomalies="[invalid_json")
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="Malformed JSON in 'anomalies.json'"):
        load_catalog("2026")


def test_load_catalog_metadata_duplicate_key(tmp_path, monkeypatch):
    raw_metadata = """{
      "pcge_version": "2026",
      "schema_version": 1,
      "dataset_revision": 1,
      "entry_count": 1,
      "entry_count": 999
    }"""
    _create_simulated_snapshot(tmp_path, "2026", metadata=raw_metadata)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(
        PCGEDataError,
        match=(
            r"Duplicate JSON key 'entry_count' in 'metadata\.json' for version '2026'"
        ),
    ):
        load_catalog("2026")


def test_load_catalog_entries_duplicate_key(tmp_path, monkeypatch):
    raw_entries = """[
      {
        "code": "1",
        "code": "9",
        "name": "Elemento",
        "parent_code": null
      }
    ]"""
    _create_simulated_snapshot(
        tmp_path,
        "2026",
        entries=raw_entries,
        metadata={
            "pcge_version": "2026",
            "schema_version": 1,
            "dataset_revision": 1,
            "entry_count": 1,
        },
    )
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(
        PCGEDataError,
        match=r"Duplicate JSON key 'code' in 'entries\.json' for version '2026'",
    ):
        load_catalog("2026")


def test_load_catalog_source_duplicate_key(tmp_path, monkeypatch):
    calc_sha = hashlib.sha256(b"[]").hexdigest().upper()
    raw_source = f"""{{
      "title": "Plan Contable",
      "title": "Plan Contable 2",
      "authority": "Consejo",
      "resolution": "Res 1",
      "resolution_date": "2026-01-01",
      "publication_date": "2026-01-02",
      "mandatory_effective_date": "2026-01-03",
      "resolution_url": "https://example.com",
      "source_filename": "file.pdf",
      "source_sha256": "{"A" * 64}",
      "dataset_sha256": "{calc_sha}",
      "catalog_chapter": "Cap II",
      "catalog_pdf_pages": {{"first": 1, "last": 10}},
      "catalog_printed_pages": {{"first": 1, "last": 10}}
    }}"""
    _create_simulated_snapshot(tmp_path, "2026", source=raw_source)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(
        PCGEDataError,
        match=r"Duplicate JSON key 'title' in 'source\.json' for version '2026'",
    ):
        load_catalog("2026")


def test_load_catalog_anomalies_duplicate_key(tmp_path, monkeypatch):
    raw_anomalies = """[
      {
        "id": "A-1",
        "id": "A-2",
        "type": "dup",
        "code": "10",
        "status": "unresolved",
        "description": "desc",
        "decision": "dec",
        "confirmation_no_invented_code": "conf",
        "occurrences": []
      }
    ]"""
    _create_simulated_snapshot(tmp_path, "2026", anomalies=raw_anomalies)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(
        PCGEDataError,
        match=r"Duplicate JSON key 'id' in 'anomalies\.json' for version '2026'",
    ):
        load_catalog("2026")


def test_load_catalog_source_not_object(tmp_path, monkeypatch):
    _create_simulated_snapshot(tmp_path, "2026", source="[1, 2, 3]")
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="source.json.*must contain a JSON object"):
        load_catalog("2026")


def test_load_catalog_source_missing_keys(tmp_path, monkeypatch):
    _create_simulated_snapshot(tmp_path, "2026", source={"title": "Incomplete"})
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="source.json.*missing required keys"):
        load_catalog("2026")


def test_load_catalog_source_extra_keys(tmp_path, monkeypatch):
    vdir = tmp_path / "2026"
    vdir.mkdir(parents=True, exist_ok=True)
    _create_simulated_snapshot(tmp_path, "2026")
    source_json = json.loads((vdir / "source.json").read_text(encoding="utf-8"))
    source_json["extra_key"] = "unexpected"
    (vdir / "source.json").write_text(json.dumps(source_json), encoding="utf-8")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="source.json.*unexpected extra keys"):
        load_catalog("2026")


def test_load_catalog_source_invalid_date_type(tmp_path, monkeypatch):
    vdir = tmp_path / "2026"
    _create_simulated_snapshot(tmp_path, "2026")
    source_json = json.loads((vdir / "source.json").read_text(encoding="utf-8"))
    source_json["resolution_date"] = 12345
    (vdir / "source.json").write_text(json.dumps(source_json), encoding="utf-8")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="must be a str"):
        load_catalog("2026")


def test_load_catalog_source_invalid_calendar_date(tmp_path, monkeypatch):
    vdir = tmp_path / "2026"
    _create_simulated_snapshot(tmp_path, "2026")
    source_json = json.loads((vdir / "source.json").read_text(encoding="utf-8"))
    source_json["resolution_date"] = "2026-02-30"
    (vdir / "source.json").write_text(json.dumps(source_json), encoding="utf-8")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="invalid date format"):
        load_catalog("2026")


@pytest.mark.parametrize(
    "invalid_date",
    [
        "20190516",
        "2019-W20-4",
        "2019-02-30",
    ],
)
@pytest.mark.parametrize(
    "date_field",
    [
        "resolution_date",
        "publication_date",
        "mandatory_effective_date",
    ],
)
def test_load_catalog_source_invalid_date_format(
    tmp_path, monkeypatch, date_field, invalid_date
):
    vdir = tmp_path / "2026"
    _create_simulated_snapshot(tmp_path, "2026")
    source_json = json.loads((vdir / "source.json").read_text(encoding="utf-8"))
    source_json[date_field] = invalid_date
    (vdir / "source.json").write_text(json.dumps(source_json), encoding="utf-8")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError) as exc_info:
        load_catalog("2026")
    msg = str(exc_info.value)
    assert "source.json" in msg
    assert "2026" in msg
    assert date_field in msg
    assert "invalid date format" in msg


def test_load_catalog_source_malformed_page_range(tmp_path, monkeypatch):
    vdir = tmp_path / "2026"
    _create_simulated_snapshot(tmp_path, "2026")
    source_json = json.loads((vdir / "source.json").read_text(encoding="utf-8"))
    source_json["catalog_pdf_pages"] = {"first": 10, "last": 1}
    (vdir / "source.json").write_text(json.dumps(source_json), encoding="utf-8")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="first page.*cannot be greater"):
        load_catalog("2026")


def test_load_catalog_dataset_sha256_mismatch(tmp_path, monkeypatch):
    vdir = tmp_path / "2026"
    _create_simulated_snapshot(tmp_path, "2026")
    source_json = json.loads((vdir / "source.json").read_text(encoding="utf-8"))
    source_json["dataset_sha256"] = "B" * 64
    (vdir / "source.json").write_text(json.dumps(source_json), encoding="utf-8")

    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="Integrity check failed.*mismatch"):
        load_catalog("2026")


def test_load_catalog_anomalies_not_array(tmp_path, monkeypatch):
    _create_simulated_snapshot(tmp_path, "2026", anomalies={"id": "A1"})
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(
        PCGEDataError, match="anomalies.json.*must contain a JSON array"
    ):
        load_catalog("2026")


def test_load_catalog_anomalies_both_code_and_codes(tmp_path, monkeypatch):
    anom = [
        {
            "id": "A1",
            "type": "dup",
            "code": "10",
            "codes": ["10"],
            "status": "unresolved",
            "description": "desc",
            "decision": "dec",
            "confirmation_no_invented_code": "conf",
            "occurrences": [],
        }
    ]
    _create_simulated_snapshot(tmp_path, "2026", anomalies=anom)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="cannot contain both 'code' and 'codes'"):
        load_catalog("2026")


def test_load_catalog_anomalies_neither_code_nor_codes(tmp_path, monkeypatch):
    anom = [
        {
            "id": "A1",
            "type": "dup",
            "status": "unresolved",
            "description": "desc",
            "decision": "dec",
            "confirmation_no_invented_code": "conf",
            "occurrences": [],
        }
    ]
    _create_simulated_snapshot(tmp_path, "2026", anomalies=anom)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="must contain either 'code' or 'codes'"):
        load_catalog("2026")


def test_load_catalog_anomalies_extra_field(tmp_path, monkeypatch):
    anom = [
        {
            "id": "A1",
            "type": "dup",
            "code": "10",
            "status": "unresolved",
            "description": "desc",
            "decision": "dec",
            "confirmation_no_invented_code": "conf",
            "occurrences": [],
            "extra_field": 123,
        }
    ]
    _create_simulated_snapshot(tmp_path, "2026", anomalies=anom)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="unexpected extra keys"):
        load_catalog("2026")


def test_load_catalog_anomalies_occurrence_extra_field(tmp_path, monkeypatch):
    anom = [
        {
            "id": "A1",
            "type": "dup",
            "code": "10",
            "status": "unresolved",
            "description": "desc",
            "decision": "dec",
            "confirmation_no_invented_code": "conf",
            "occurrences": [
                {
                    "occurrence_index": 1,
                    "pdf_page": 1,
                    "printed_page": 1,
                    "printed_code": "10",
                    "printed_name": "Name",
                    "printed_parent_code": "1",
                    "disposition": "retained",
                    "unexpected": True,
                }
            ],
        }
    ]
    _create_simulated_snapshot(tmp_path, "2026", anomalies=anom)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="unexpected extra keys"):
        load_catalog("2026")


def test_load_catalog_anomalies_validation_error_wrapped(tmp_path, monkeypatch):
    anom = [
        {
            "id": "A1",
            "type": "dup",
            "code": "10",
            "status": "unresolved",
            "description": "desc",
            "decision": "dec",
            "confirmation_no_invented_code": "conf",
            "occurrences": [
                {
                    "occurrence_index": 0,  # Invalid: < 1
                    "pdf_page": 1,
                    "printed_page": 1,
                    "printed_code": "10",
                    "printed_name": "Name",
                    "printed_parent_code": "1",
                    "disposition": "retained",
                }
            ],
        }
    ]
    _create_simulated_snapshot(tmp_path, "2026", anomalies=anom)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="Invalid occurrence in 'anomalies.json'"):
        load_catalog("2026")


def test_load_catalog_nested_object_duplicate_key(tmp_path, monkeypatch):
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
    _create_simulated_snapshot(
        tmp_path,
        "2026",
        entries=raw_entries,
        metadata={
            "pcge_version": "2026",
            "schema_version": 1,
            "dataset_revision": 1,
            "entry_count": 1,
        },
    )
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(
        PCGEDataError,
        match=r"Duplicate JSON key 'tag' in 'entries\.json' for version '2026'",
    ):
        load_catalog("2026")


def test_load_catalog_metadata_not_object(tmp_path, monkeypatch):
    _create_simulated_snapshot(tmp_path, "2026", metadata="[1, 2, 3]")
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="must contain a JSON object"):
        load_catalog("2026")


def test_load_catalog_entries_not_array(tmp_path, monkeypatch):
    _create_simulated_snapshot(
        tmp_path,
        "2026",
        entries='{"code": "1"}',
        metadata={
            "pcge_version": "2026",
            "schema_version": 1,
            "dataset_revision": 1,
            "entry_count": 0,
        },
    )
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="must contain a JSON array"):
        load_catalog("2026")


def test_load_catalog_metadata_missing_keys(tmp_path, monkeypatch):
    # Missing entry_count
    meta_json = {
        "pcge_version": "2026",
        "schema_version": 1,
        "dataset_revision": 1,
    }
    _create_simulated_snapshot(tmp_path, "2026", metadata=meta_json)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="missing required keys.*entry_count"):
        load_catalog("2026")


def test_load_catalog_metadata_extra_keys(tmp_path, monkeypatch):
    meta_json = {
        "pcge_version": "2026",
        "schema_version": 1,
        "dataset_revision": 1,
        "entry_count": 0,
        "unexpected_extra": "foo",
    }
    _create_simulated_snapshot(tmp_path, "2026", metadata=meta_json)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="unexpected extra keys"):
        load_catalog("2026")


def test_load_catalog_metadata_bool_for_integer(tmp_path, monkeypatch):
    meta_json = {
        "pcge_version": "2026",
        "schema_version": True,
        "dataset_revision": 1,
        "entry_count": 0,
    }
    _create_simulated_snapshot(tmp_path, "2026", metadata=meta_json)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="must be an integer, got bool"):
        load_catalog("2026")


def test_load_catalog_entries_element_not_object(tmp_path, monkeypatch):
    entries_json = [
        {"code": "1", "name": "Activo", "parent_code": None},
        "not_an_object",
    ]
    _create_simulated_snapshot(tmp_path, "2026", entries=entries_json)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="index 1.*must be a JSON object"):
        load_catalog("2026")


def test_load_catalog_entries_missing_key_includes_index(tmp_path, monkeypatch):
    entries_json = [
        {"code": "1", "name": "Activo", "parent_code": None},
        {"code": "10", "name": "Efectivo"},  # missing parent_code
    ]
    _create_simulated_snapshot(tmp_path, "2026", entries=entries_json)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(
        PCGEDataError, match=r"at index 1 missing keys: \['parent_code'\]"
    ):
        load_catalog("2026")


def test_load_catalog_version_mismatch(tmp_path, monkeypatch):
    meta_json = {
        "pcge_version": "2025",  # Mismatch with requested 2026
        "schema_version": 1,
        "dataset_revision": 1,
        "entry_count": 0,
    }
    _create_simulated_snapshot(tmp_path, "2026", metadata=meta_json)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="does not match requested version"):
        load_catalog("2026")


def test_load_catalog_semantic_error_propagated_as_pcge_data_error(
    tmp_path, monkeypatch
):
    entries_json = [
        {"code": "1", "name": "Activo", "parent_code": None},
        {"code": "20", "name": "Mercaderías", "parent_code": "1"},  # Prefix mismatch!
    ]
    _create_simulated_snapshot(tmp_path, "2026", entries=entries_json)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="expected prefix"):
        load_catalog("2026")


def test_load_catalog_unsupported_schema_version(tmp_path, monkeypatch):
    meta_json = {
        "pcge_version": "2026",
        "schema_version": 2,
        "dataset_revision": 1,
        "entry_count": 1,
    }
    entries_json = [
        {"code": "1", "name": "Activo", "parent_code": None},
    ]
    _create_simulated_snapshot(
        tmp_path, "2026", metadata=meta_json, entries=entries_json
    )
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="Unsupported schema_version"):
        load_catalog("2026")


def test_load_catalog_code_with_more_than_six_digits(tmp_path, monkeypatch):
    entries_json = [
        {"code": "6", "name": "Elemento", "parent_code": None},
        {"code": "6551111", "name": "Sintético 7 dígitos", "parent_code": "655111"},
    ]
    _create_simulated_snapshot(tmp_path, "2026", entries=entries_json)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="Invalid code length"):
        load_catalog("2026")


def test_load_catalog_duplicate_code_wrapped_in_data_error(tmp_path, monkeypatch):
    entries_json = [
        {"code": "1", "name": "Activo", "parent_code": None},
        {"code": "1", "name": "Activo duplicado", "parent_code": None},
    ]
    _create_simulated_snapshot(tmp_path, "2026", entries=entries_json)
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="Duplicate code"):
        load_catalog("2026")


def test_load_catalog_entry_count_mismatch_wrapped_in_data_error(tmp_path, monkeypatch):
    meta_json = {
        "pcge_version": "2026",
        "schema_version": 1,
        "dataset_revision": 1,
        "entry_count": 5,
    }
    entries_json = [
        {"code": "1", "name": "Activo", "parent_code": None},
    ]
    _create_simulated_snapshot(
        tmp_path, "2026", metadata=meta_json, entries=entries_json
    )
    monkeypatch.setattr("pcge.loader.importlib_resources.files", lambda pkg: tmp_path)

    with pytest.raises(PCGEDataError, match="metadata.entry_count"):
        load_catalog("2026")


def test_available_versions_matches_packaged_resource_directories():
    resources = importlib_resources.files("pcge.data")
    versions = tuple(
        sorted(
            child.name
            for child in resources.iterdir()
            if child.is_dir() and child.name.isascii() and child.name.isdigit()
        )
    )
    assert versions == available_versions()
