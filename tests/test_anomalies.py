import pytest

from pcge import load_catalog
from pcge.anomalies import PCGEAnomaly, PCGEAnomalyOccurrence


def _make_valid_occurrence(**kwargs):
    defaults = {
        "occurrence_index": 1,
        "pdf_page": 48,
        "printed_page": 46,
        "printed_code": "70992",
        "printed_name": "Relacionadas",
        "printed_parent_code": "7090",
        "disposition": "excluded_from_canonical_catalog",
    }
    defaults.update(kwargs)
    return PCGEAnomalyOccurrence(**defaults)


def _make_valid_anomaly(**kwargs):
    defaults = {
        "id": "ANOMALY-2026-70992",
        "type": "duplicate_code",
        "codes": ("70992",),
        "status": "unresolved_source_anomaly",
        "description": "El código 70992 está impreso en dos ubicaciones distintas.",
        "decision": "Se conserva la segunda aparición.",
        "confirmation_no_invented_code": (
            "Se confirma que el código 70902 no fue creado."
        ),
        "occurrences": (_make_valid_occurrence(),),
    }
    defaults.update(kwargs)
    return PCGEAnomaly(**defaults)


def test_occurrence_valid_construction():
    occ = _make_valid_occurrence()
    assert occ.occurrence_index == 1
    assert occ.pdf_page == 48
    assert occ.printed_code == "70992"


def test_occurrence_frozen():
    occ = _make_valid_occurrence()
    with pytest.raises((AttributeError, TypeError)):
        occ.printed_code = "123"  # type: ignore[misc]


@pytest.mark.parametrize("field", ["occurrence_index", "pdf_page", "printed_page"])
@pytest.mark.parametrize("invalid_val", [0, -1, True, False, "1", None])
def test_occurrence_rejects_invalid_integers(field, invalid_val):
    with pytest.raises((TypeError, ValueError)):
        _make_valid_occurrence(**{field: invalid_val})


@pytest.mark.parametrize(
    "field", ["printed_code", "printed_name", "printed_parent_code", "disposition"]
)
@pytest.mark.parametrize("invalid_val", ["", 123, None])
def test_occurrence_rejects_invalid_strings(field, invalid_val):
    with pytest.raises((TypeError, ValueError)):
        _make_valid_occurrence(**{field: invalid_val})


def test_occurrence_rejects_none_printed_parent_code():
    with pytest.raises(TypeError, match="printed_parent_code must be a str"):
        _make_valid_occurrence(printed_parent_code=None)


def test_occurrence_rejects_whitespace_printed_parent_code():
    with pytest.raises(
        ValueError, match="printed_parent_code cannot be empty or whitespace only"
    ):
        _make_valid_occurrence(printed_parent_code="   ")


def test_occurrence_rejects_whitespace_only_strings():
    for fld in [
        "printed_code",
        "printed_name",
        "printed_parent_code",
        "disposition",
    ]:
        with pytest.raises(ValueError):
            _make_valid_occurrence(**{fld: "   "})


def test_anomaly_valid_construction():
    anom = _make_valid_anomaly()
    assert anom.id == "ANOMALY-2026-70992"
    assert anom.codes == ("70992",)
    assert len(anom.occurrences) == 1


def test_anomaly_frozen():
    anom = _make_valid_anomaly()
    with pytest.raises((AttributeError, TypeError)):
        anom.id = "OTHER"  # type: ignore[misc]


def test_anomaly_rejects_list_for_codes():
    with pytest.raises(TypeError, match="codes"):
        _make_valid_anomaly(codes=["70992"])  # type: ignore[arg-type]


def test_anomaly_rejects_empty_codes():
    with pytest.raises(ValueError, match="codes"):
        _make_valid_anomaly(codes=())


def test_anomaly_rejects_duplicate_codes():
    with pytest.raises(ValueError, match="Duplicate"):
        _make_valid_anomaly(codes=("70992", "70992"))


def test_anomaly_rejects_list_for_occurrences():
    occ = _make_valid_occurrence()
    with pytest.raises(TypeError, match="occurrences"):
        _make_valid_anomaly(occurrences=[occ])  # type: ignore[arg-type]


def test_anomaly_rejects_empty_occurrences():
    with pytest.raises(ValueError, match="occurrences"):
        _make_valid_anomaly(occurrences=())


def test_anomaly_rejects_non_occurrence_elements():
    with pytest.raises(TypeError, match="PCGEAnomalyOccurrence"):
        _make_valid_anomaly(occurrences=("not_an_occurrence",))  # type: ignore[arg-type]


def test_anomaly_rejects_duplicate_occurrence_index():
    occ1 = _make_valid_occurrence(occurrence_index=1)
    occ2 = _make_valid_occurrence(occurrence_index=1, pdf_page=49)
    with pytest.raises(ValueError, match="Duplicate occurrence_index"):
        _make_valid_anomaly(occurrences=(occ1, occ2))


def test_official_catalogs_anomalies_counts():
    cat_2019 = load_catalog("2019")
    cat_2026 = load_catalog("2026")

    assert len(cat_2019.anomalies) == 10
    assert len(cat_2026.anomalies) == 1


def test_official_catalogs_anomalies_for_real_cases():
    cat_2019 = load_catalog("2019")
    cat_2026 = load_catalog("2026")

    # 1. 63432 is NOT in 2019 catalog, but anomalies_for finds it
    assert "63432" not in cat_2019
    res_63432 = cat_2019.anomalies_for("63432")
    assert len(res_63432) == 1
    assert res_63432[0].id == "ANOMALY-2019-63432"

    # 2. 61 is in 2019 catalog, has nomenclature discrepancy anomaly
    assert "61" in cat_2019
    res_61 = cat_2019.anomalies_for("61")
    assert len(res_61) == 1
    assert res_61[0].id == "ANOMALY-2019-NOMENCLATURE-61-85-88"

    # 3. 70992 in 2026 catalog has duplicate code anomaly
    assert "70992" in cat_2026
    res_70992 = cat_2026.anomalies_for("70992")
    assert len(res_70992) == 1
    assert res_70992[0].id == "ANOMALY-2026-70992"

    # 4. 99999 has no anomalies in 2026
    assert cat_2026.anomalies_for("99999") == ()

    # 5. Non-hierarchical matching assertions: exact match only
    assert cat_2019.anomalies_for("6343") == ()
    assert cat_2019.anomalies_for("634321") == ()
    assert cat_2026.anomalies_for("7099") == ()


def test_anomaly_non_numeric_code_is_valid():
    anom = _make_valid_anomaly(codes=("ERR-63432",))
    assert anom.codes == ("ERR-63432",)


def test_anomaly_rejects_empty_and_whitespace_codes():
    with pytest.raises(ValueError, match="cannot be empty"):
        _make_valid_anomaly(codes=("",))
    with pytest.raises(ValueError, match="cannot be whitespace only"):
        _make_valid_anomaly(codes=("   ",))
