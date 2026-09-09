import json
from pathlib import Path

import pytest

from pcge import PCGECatalog, PCGELevel, load_catalog

REPO_ROOT = Path(__file__).resolve().parent.parent

OFFICIAL_SIX_DIGIT_CODES = {
    "655111": "Operación",
    "655112": "Inversión",
    "655121": "Operación",
    "655122": "Inversión",
    "655131": "Operación",
    "655132": "Inversión",
    "655141": "Operación",
    "655142": "Inversión",
    "655151": "Operación",
    "655152": "Inversión",
    "655161": "Operación",
    "655162": "Inversión",
}

EXPECTED_ROOT_ELEMENTS = {
    "1": "ACTIVO DISPONIBLE Y EXIGIBLE",
    "2": "ACTIVO REALIZABLE",
    "3": "ACTIVO INMOVILIZADO",
    "4": "PASIVO",
    "5": "PATRIMONIO",
    "6": "GASTOS POR NATURALEZA",
    "7": "INGRESOS POR NATURALEZA",
    "8": (
        "SALDOS INTERMEDIARIOS DE GESTIÓN Y DETERMINACIÓN DEL RESULTADO DEL EJERCICIO"
    ),
    "9": "GASTOS POR CATEGORÍA",
}


@pytest.fixture(scope="module")
def catalog_2026() -> PCGECatalog:
    return load_catalog("2026")


def test_01_load_catalog_success(catalog_2026: PCGECatalog):
    assert isinstance(catalog_2026, PCGECatalog)
    assert len(catalog_2026) == 1636


def test_02_catalog_metadata_exists(catalog_2026: PCGECatalog):
    assert catalog_2026.metadata is not None


def test_03_pcge_version_2026(catalog_2026: PCGECatalog):
    assert catalog_2026.metadata is not None
    assert catalog_2026.metadata.pcge_version == "2026"


def test_04_schema_version_is_one(catalog_2026: PCGECatalog):
    assert catalog_2026.metadata is not None
    assert catalog_2026.metadata.schema_version == 1


def test_05_dataset_revision_is_one(catalog_2026: PCGECatalog):
    assert catalog_2026.metadata is not None
    assert catalog_2026.metadata.dataset_revision == 1


def test_06_entry_count_matches_catalog_len(catalog_2026: PCGECatalog):
    assert catalog_2026.metadata is not None
    assert catalog_2026.metadata.entry_count == len(catalog_2026)


def test_07_catalog_is_not_empty(catalog_2026: PCGECatalog):
    assert len(catalog_2026) > 0


def test_08_all_codes_are_unique(catalog_2026: PCGECatalog):
    codes = [entry.code for entry in catalog_2026]
    assert len(codes) == len(set(codes))


def test_09_all_parents_exist(catalog_2026: PCGECatalog):
    for entry in catalog_2026:
        if entry.parent_code is not None:
            assert entry.parent_code in catalog_2026
            parent_entry = catalog_2026[entry.parent_code]
            assert parent_entry.code == entry.parent_code


def test_10_canonical_prefix_rule(catalog_2026: PCGECatalog):
    for entry in catalog_2026:
        if entry.parent_code is None:
            assert entry.code in EXPECTED_ROOT_ELEMENTS
        else:
            assert entry.parent_code == entry.code[:-1]


def test_11_codes_length_between_one_and_six(catalog_2026: PCGECatalog):
    lengths = {entry.code_length for entry in catalog_2026}
    assert lengths == {1, 2, 3, 4, 5, 6}
    for entry in catalog_2026:
        assert 1 <= entry.code_length <= 6


def test_12_expected_root_elements(catalog_2026: PCGECatalog):
    root_entries = [e for e in catalog_2026 if e.parent_code is None]
    assert len(root_entries) == 9
    root_dict = {e.code: e.name for e in root_entries}
    assert root_dict == EXPECTED_ROOT_ELEMENTS
    for code, expected_name in EXPECTED_ROOT_ELEMENTS.items():
        assert catalog_2026[code].name == expected_name
        assert catalog_2026[code].pcge_level is PCGELevel.ELEMENT


def test_13_official_six_digit_codes_exact_set(catalog_2026: PCGECatalog):
    six_digit_entries = [e for e in catalog_2026 if e.code_length == 6]
    assert len(six_digit_entries) == 12
    six_digit_dict = {e.code: e.name for e in six_digit_entries}
    assert six_digit_dict == OFFICIAL_SIX_DIGIT_CODES


def test_14_six_digit_codes_pcge_level_is_none(catalog_2026: PCGECatalog):
    for code in OFFICIAL_SIX_DIGIT_CODES:
        entry = catalog_2026[code]
        assert entry.pcge_level is None
        assert entry.code_length == 6
        assert entry.parent_code == code[:-1]


def test_15_code_70992_exists_exactly_once(catalog_2026: PCGECatalog):
    matches = [e for e in catalog_2026 if e.code == "70992"]
    assert len(matches) == 1


def test_16_code_70992_metadata_and_parent(catalog_2026: PCGECatalog):
    entry_70992 = catalog_2026["70992"]
    assert entry_70992.name == "Contrato de consultoría TI"
    assert entry_70992.parent_code == "7099"
    assert entry_70992.pcge_level is PCGELevel.SUBDIVISIONARY


def test_17_code_70902_does_not_exist(catalog_2026: PCGECatalog):
    assert "70902" not in catalog_2026
    matches = [e for e in catalog_2026 if e.code == "70902"]
    assert len(matches) == 0


def test_18_anomaly_documented_in_anomalies_json():
    anomalies_file = REPO_ROOT / "sources" / "2026" / "anomalies.json"
    assert anomalies_file.is_file()
    with anomalies_file.open(encoding="utf-8") as f:
        anomalies = json.load(f)

    assert isinstance(anomalies, list)
    assert len(anomalies) >= 1

    anomaly_70992 = next((a for a in anomalies if a["code"] == "70992"), None)
    assert anomaly_70992 is not None
    assert anomaly_70992["type"] == "duplicate_code"
    assert anomaly_70992["status"] == "unresolved_source_anomaly"
    assert "70902" in anomaly_70992["confirmation_no_invented_code"]

    occurrences = anomaly_70992["occurrences"]
    assert len(occurrences) == 2

    occ1 = occurrences[0]
    assert occ1["pdf_page"] == 48
    assert occ1["printed_page"] == 46
    assert occ1["printed_name"] == "Relacionadas"
    assert occ1["printed_parent_code"] == "7090"
    assert occ1["disposition"] == "excluded_from_canonical_catalog"

    occ2 = occurrences[1]
    assert occ2["pdf_page"] == 49
    assert occ2["printed_page"] == 47
    assert occ2["printed_name"] == "Contrato de consultoría TI"
    assert occ2["printed_parent_code"] == "7099"
    assert occ2["disposition"] == "retained_in_canonical_catalog"


def test_19_real_hierarchical_navigation(catalog_2026: PCGECatalog):
    entry_655111 = catalog_2026["655111"]
    assert entry_655111.code == "655111"
    parent_65511 = catalog_2026.parent("655111")
    assert parent_65511 is not None
    assert parent_65511.code == "65511"

    ancestors = catalog_2026.ancestors("655111")
    ancestor_codes = [a.code for a in ancestors]
    # ancestors() returns closest parent first
    assert ancestor_codes == ["65511", "6551", "655", "65", "6"]

    children_65511 = catalog_2026.children("65511")
    children_codes = [c.code for c in children_65511]
    assert "655111" in children_codes
    assert "655112" in children_codes

    descendants_9 = catalog_2026.descendants("9")
    descendant_codes_9 = [d.code for d in descendants_9]
    assert descendant_codes_9 == ["91", "92", "93"]

    assert catalog_2026.parent("1") is None
    assert catalog_2026.ancestors("1") == ()


def test_20_real_search_functionality(catalog_2026: PCGECatalog):
    results_code = catalog_2026.search("655111")
    assert len(results_code) >= 1
    assert any(e.code == "655111" for e in results_code)

    results_consultoria = catalog_2026.search("consultoría")
    assert any(e.code == "70992" for e in results_consultoria)

    results_lower = catalog_2026.search("mercaderías")
    results_upper = catalog_2026.search("MERCADERÍAS")
    assert [e.code for e in results_lower] == [e.code for e in results_upper]
    assert "201" in [e.code for e in results_lower]

    results_unaccented = catalog_2026.search("mercaderias")
    assert [e.code for e in results_unaccented] == [e.code for e in results_lower]
    # Both "20" (MERCADERIAS) and "201" (Mercaderías) match "mercaderias"
    assert "20" in [e.code for e in results_unaccented]
    assert "201" in [e.code for e in results_unaccented]

    results_inversion = catalog_2026.search("inversion")
    assert any(e.code == "655112" for e in results_inversion)


def test_21_representative_entries_match_pdf(catalog_2026: PCGECatalog):
    assert catalog_2026["10"].name == "EFECTIVO Y EQUIVALENTES AL EFECTIVO"
    assert catalog_2026["101"].name == "Caja"
    assert catalog_2026["1041"].name == "Cuentas corrientes operativas"

    # In PDF p. 22: code 20 is printed as "MERCADERIAS" (without accent)
    assert catalog_2026["20"].name == "MERCADERIAS"
    assert catalog_2026["201"].name == "Mercaderías"
    assert catalog_2026["20111"].name == "Costo"

    assert catalog_2026["33"].name == "PROPIEDADES, PLANTA Y EQUIPO"
    assert catalog_2026["331"].name == "Terrenos"
    assert catalog_2026["3311"].name == "Terrenos"

    assert catalog_2026["40"].name == (
        "TRIBUTOS, CONTRAPRESTACIONES Y APORTES AL SISTEMA PÚBLICO "
        "DE PENSIONES Y DE SALUD POR PAGAR"
    )
    assert catalog_2026["40111"].name == "IGV – Cuenta propia"

    assert catalog_2026["50"].name == "CAPITAL"
    assert catalog_2026["501"].name == "Capital social"
    assert catalog_2026["5011"].name == "Acciones"

    assert catalog_2026["60"].name == "COMPRAS"
    assert catalog_2026["601"].name == "Mercaderías"
    assert catalog_2026["6093"].name == (
        "Costos vinculados con las compras de materiales, suministros y repuestos"
    )
    assert catalog_2026["68713"].name == (
        "Cuentas por cobrar al personal, a los accionistas (socios) y directores"
    )

    assert catalog_2026["70"].name == "VENTAS"
    assert catalog_2026["701"].name == "Mercaderías"
    assert catalog_2026["70111"].name == "Terceros"

    assert catalog_2026["80"].name == "MARGEN COMERCIAL"
    assert catalog_2026["801"].name == "Margen comercial"

    assert catalog_2026["9"].name == "GASTOS POR CATEGORÍA"
    assert catalog_2026["91"].name == "GASTOS DE OPERACIÓN"
    assert catalog_2026["92"].name == "GASTOS DE INVERSIÓN"
    assert catalog_2026["93"].name == "GASTOS DE FINANCIAMIENTO"


def test_22_schemas_remain_valid_json():
    entries_schema_file = REPO_ROOT / "schemas" / "entries.schema.json"
    metadata_schema_file = REPO_ROOT / "schemas" / "metadata.schema.json"

    assert entries_schema_file.is_file()
    assert metadata_schema_file.is_file()

    with entries_schema_file.open(encoding="utf-8") as f:
        entries_schema = json.load(f)
    with metadata_schema_file.open(encoding="utf-8") as f:
        metadata_schema = json.load(f)

    assert entries_schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert entries_schema["type"] == "array"
    assert metadata_schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert metadata_schema["type"] == "object"


def test_23_source_json_contains_expected_sha256():
    source_file = REPO_ROOT / "sources" / "2026" / "source.json"
    assert source_file.is_file()

    with source_file.open(encoding="utf-8") as f:
        source_data = json.load(f)

    expected_sha256 = "48C568CA196C68348743DDA96C55C38593B0437CE732A4C5D77D7C9ACA896B19"
    assert source_data["source_sha256"] == expected_sha256
    assert source_data["title"] == "Plan Contable General Empresarial 2026"
    assert source_data["authority"] == "Consejo Normativo de Contabilidad"
    assert source_data["resolution"] == "Resolución N.° 002-2026-EF/30"
    assert source_data["catalog_pdf_pages"] == {"first": 19, "last": 52}
    assert source_data["catalog_printed_pages"] == {"first": 17, "last": 50}


def test_24_metadata_entry_count_matches_entries_json_length():
    data_dir = REPO_ROOT / "src" / "pcge" / "data" / "2026"
    entries_path = data_dir / "entries.json"
    metadata_path = data_dir / "metadata.json"

    with entries_path.open(encoding="utf-8") as f:
        entries_data = json.load(f)
    with metadata_path.open(encoding="utf-8") as f:
        metadata_data = json.load(f)

    assert isinstance(entries_data, list)
    assert isinstance(metadata_data, dict)
    assert len(entries_data) == 1636
    assert metadata_data["entry_count"] == len(entries_data)


def test_explicit_catalog_reconstruction_flow(catalog_2026: PCGECatalog):
    reconstructed = PCGECatalog(tuple(catalog_2026), metadata=catalog_2026.metadata)
    assert len(reconstructed) == 1636
    assert reconstructed.metadata == catalog_2026.metadata
