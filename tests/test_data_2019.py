import json
from pathlib import Path

import pytest

from pcge import PCGECatalog, PCGELevel, load_catalog

REPO_ROOT = Path(__file__).resolve().parent.parent

OFFICIAL_SIX_DIGIT_CODES = {
    "682111": "Costo",
    "682112": "Revaluación",
    "682113": "Costo de financiación",
    "682211": "Costo",
    "682212": "Revaluación",
    "682213": "Costo de financiación",
    "682221": "Costo",
    "682222": "Revaluación",
    "682223": "Costo de financiación",
    "682231": "Costo",
    "682232": "Revaluación",
    "682251": "Costo",
    "682252": "Revaluación",
    "683111": "Costo",
    "683112": "Revaluación",
    "683121": "Costo",
    "683122": "Revaluación",
    "683131": "Costo",
    "683132": "Revaluación",
    "683152": "Revaluación",
}

EXPECTED_ROOT_ELEMENTS = {
    "1": "ACTIVO DISPONIBLE Y EXIGIBLE",
    "2": "ACTIVO REALIZABLE",
    "3": "ACTIVO INMOVILIZADO",
    "4": "PASIVO",
    "5": "PATRIMONIO NETO",
    "6": "GASTOS POR NATURALEZA",
    "7": "INGRESOS",
    "8": (
        "SALDOS INTERMEDIARIOS DE GESTIÓN Y DETERMINACIÓN DEL RESULTADO DEL EJERCICIO"
    ),
}

EXPECTED_LENGTH_DISTRIBUTION = {
    1: 8,
    2: 74,
    3: 322,
    4: 644,
    5: 689,
    6: 20,
}


@pytest.fixture(scope="module")
def catalog_2019() -> PCGECatalog:
    return load_catalog("2019")


def test_01_load_catalog_success(catalog_2019: PCGECatalog):
    assert isinstance(catalog_2019, PCGECatalog)
    assert len(catalog_2019) == 1757


def test_02_catalog_metadata_exists(catalog_2019: PCGECatalog):
    assert catalog_2019.metadata is not None
    assert catalog_2019.metadata.pcge_version == "2019"
    assert catalog_2019.metadata.schema_version == 1
    assert catalog_2019.metadata.dataset_revision == 1
    assert catalog_2019.metadata.entry_count == 1757
    assert catalog_2019.metadata.entry_count == len(catalog_2019)


def test_03_all_codes_are_unique(catalog_2019: PCGECatalog):
    codes = [entry.code for entry in catalog_2019]
    assert len(codes) == len(set(codes))


def test_04_all_parents_exist(catalog_2019: PCGECatalog):
    for entry in catalog_2019:
        if entry.parent_code is not None:
            assert entry.parent_code in catalog_2019
            parent = catalog_2019[entry.parent_code]
            assert parent.code == entry.parent_code


def test_05_canonical_prefix_rule(catalog_2019: PCGECatalog):
    for entry in catalog_2019:
        if entry.parent_code is None:
            assert entry.code in EXPECTED_ROOT_ELEMENTS
        else:
            assert entry.parent_code == entry.code[:-1]


def test_06_root_elements(catalog_2019: PCGECatalog):
    roots = {
        entry.code: entry.name for entry in catalog_2019 if entry.parent_code is None
    }
    assert roots == EXPECTED_ROOT_ELEMENTS
    assert len(roots) == 8
    assert "0" not in catalog_2019
    assert "9" not in catalog_2019


def test_07_length_distribution(catalog_2019: PCGECatalog):
    distribution: dict[int, int] = {}
    for entry in catalog_2019:
        distribution[entry.code_length] = distribution.get(entry.code_length, 0) + 1
    assert distribution == EXPECTED_LENGTH_DISTRIBUTION


def test_08_six_digit_codes(catalog_2019: PCGECatalog):
    six_digits = {
        entry.code: entry.name for entry in catalog_2019 if entry.code_length == 6
    }
    assert len(six_digits) == 20
    assert six_digits == OFFICIAL_SIX_DIGIT_CODES
    for code in six_digits:
        entry = catalog_2019[code]
        assert entry.pcge_level is None
        assert entry.code_length == 6
        assert entry.parent_code is not None
        assert entry.parent_code in catalog_2019
        assert entry.parent_code == code[:-1]


def test_09_levels_for_standard_lengths(catalog_2019: PCGECatalog):
    expected_levels = {
        1: PCGELevel.ELEMENT,
        2: PCGELevel.ACCOUNT,
        3: PCGELevel.SUBACCOUNT,
        4: PCGELevel.DIVISIONARY,
        5: PCGELevel.SUBDIVISIONARY,
    }
    for entry in catalog_2019:
        if entry.code_length in expected_levels:
            assert entry.pcge_level == expected_levels[entry.code_length]
        else:
            assert entry.pcge_level is None


def test_10_anomalies_decisions(catalog_2019: PCGECatalog):
    # A: 27233 retained under 2723; no 27243
    assert "27233" in catalog_2019
    assert catalog_2019["27233"].parent_code == "2723"
    assert "27243" not in catalog_2019

    # B: 30221 and 30224 retained under 3022; no 30111 or 30114
    assert "30221" in catalog_2019
    assert catalog_2019["30221"].parent_code == "3022"
    assert "30224" in catalog_2019
    assert catalog_2019["30224"].parent_code == "3022"
    assert "30111" not in catalog_2019
    assert "30114" not in catalog_2019

    # C: 33404 excluded; no 36404
    assert "33404" not in catalog_2019
    assert "36404" not in catalog_2019

    # D: 38472, 38473, 38474 excluded; no 36472, 36473, 36474
    for c in ("38472", "38473", "38474", "36472", "36473", "36474"):
        assert c not in catalog_2019

    # E: 38352 excluded; no 39352
    assert "38352" not in catalog_2019
    assert "39352" not in catalog_2019

    # F: 63432 excluded; no 63422
    assert "63432" not in catalog_2019
    assert "63422" not in catalog_2019

    # G: 683351 excluded; 683152 retained; no 683151
    assert "683351" not in catalog_2019
    assert "683151" not in catalog_2019
    assert "683152" in catalog_2019
    assert catalog_2019["683152"].parent_code == "68315"

    # H: 6882 retained as lease impairment with 68820..68828;
    # 6881, 68812, 68813 excluded
    assert "6882" in catalog_2019
    assert (
        catalog_2019["6882"].name
        == "Desvalorización de activos por derecho de uso - arrendamiento financiero"
    )
    assert "6881" not in catalog_2019
    assert "68812" not in catalog_2019
    assert "68813" not in catalog_2019
    for sub in (
        "68820",
        "68821",
        "68822",
        "68823",
        "68824",
        "68825",
        "68826",
        "68827",
        "68828",
    ):
        assert sub in catalog_2019
        assert catalog_2019[sub].parent_code == "6882"

    # I: 70111 and 70112 retained under 7011; no 70121 or 70122
    assert "70111" in catalog_2019
    assert catalog_2019["70111"].parent_code == "7011"
    assert "70112" in catalog_2019
    assert catalog_2019["70112"].parent_code == "7011"
    assert "70121" not in catalog_2019
    assert "70122" not in catalog_2019


def test_11_nomenclature_uses_detailed_catalog_for_canonicalization(
    catalog_2019: PCGECatalog,
):
    # Canonical dataset uses nomenclature from the detailed catalog
    assert catalog_2019["61"].name == "VARIACIÓN DE INVENTARIOS"
    assert catalog_2019["85"].name == "RESULTADO ANTES DE IMPUESTO A LAS GANANCIAS"
    assert catalog_2019["88"].name == "IMPUESTO A LAS GANANCIAS"


def test_12_representative_names_across_elements(catalog_2019: PCGECatalog):
    samples = {
        "1": "ACTIVO DISPONIBLE Y EXIGIBLE",
        "10": "EFECTIVO Y EQUIVALENTES DE EFECTIVO",
        "101": "Caja",
        "2": "ACTIVO REALIZABLE",
        "20": "MERCADERÍAS",
        "201": "Mercaderías",
        "3": "ACTIVO INMOVILIZADO",
        "33": "PROPIEDAD, PLANTA Y EQUIPO",
        "331": "Terrenos",
        "4": "PASIVO",
        "40": (
            "TRIBUTOS, CONTRAPRESTACIONES Y APORTES AL SISTEMA PÚBLICO DE "
            "PENSIONES Y DE SALUD POR PAGAR"
        ),
        "42": "CUENTAS POR PAGAR COMERCIALES TERCEROS",
        "5": "PATRIMONIO NETO",
        "50": "CAPITAL",
        "501": "Capital social",
        "6": "GASTOS POR NATURALEZA",
        "60": "COMPRAS",
        "62": "GASTOS DE PERSONAL Y DIRECTORES",
        "7": "INGRESOS",
        "70": "VENTAS",
        "701": "Mercaderías",
        "8": (
            "SALDOS INTERMEDIARIOS DE GESTIÓN Y DETERMINACIÓN DEL "
            "RESULTADO DEL EJERCICIO"
        ),
        "80": "MARGEN COMERCIAL",
        "89": "DETERMINACIÓN DEL RESULTADO DEL EJERCICIO",
        "11111": "Costo",
        "682111": "Costo",
    }
    for code, expected_name in samples.items():
        assert code in catalog_2019
        assert catalog_2019[code].name == expected_name


def test_13_documentary_order_preservation(catalog_2019: PCGECatalog):
    entries_file = REPO_ROOT / "src" / "pcge" / "data" / "2019" / "entries.json"
    with entries_file.open(encoding="utf-8") as f:
        file_entries = json.load(f)

    expected_codes = [e["code"] for e in file_entries]
    actual_codes = [entry.code for entry in catalog_2019]
    assert actual_codes == expected_codes
    assert actual_codes[0] == "1"
    assert actual_codes[-1] == "892"


def test_14_navigation(catalog_2019: PCGECatalog):
    # parent
    assert catalog_2019.parent("1") is None
    assert catalog_2019.parent("11") == catalog_2019["1"]
    assert catalog_2019.parent("111") == catalog_2019["11"]
    assert catalog_2019.parent("1111") == catalog_2019["111"]
    assert catalog_2019.parent("11111") == catalog_2019["1111"]

    # ancestors
    ancestors = catalog_2019.ancestors("11111")
    ancestor_codes = [a.code for a in ancestors]
    assert ancestor_codes == ["1111", "111", "11", "1"]

    # children
    children_11 = catalog_2019.children("11")
    children_11_codes = [c.code for c in children_11]
    assert children_11_codes == ["111", "112", "113"]

    # descendants
    descendants_89 = catalog_2019.descendants("89")
    desc_89_codes = [d.code for d in descendants_89]
    assert desc_89_codes == ["891", "892"]


def test_15_search_normalized(catalog_2019: PCGECatalog):
    # Accents and case insensitive search
    res_transito = catalog_2019.search("transito")
    assert len(res_transito) > 0
    codes_transito = {r.code for r in res_transito}
    assert "103" in codes_transito
    assert "1031" in codes_transito
    assert "1032" in codes_transito

    res_TRANSITO = catalog_2019.search("TRÁNSITO")
    assert res_TRANSITO == res_transito

    res_mercaderias = catalog_2019.search("mercaderias")
    codes_mercaderias = {r.code for r in res_mercaderias}
    assert "20" in codes_mercaderias
    assert "201" in codes_mercaderias
    assert "701" in codes_mercaderias
