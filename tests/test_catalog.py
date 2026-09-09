import pytest

from pcge import PCGECatalog, PCGEEntry, PCGEMetadata


@pytest.fixture
def sample_entries() -> list[PCGEEntry]:
    return [
        PCGEEntry(code="1", name="Activo", parent_code=None),
        PCGEEntry(
            code="10", name="Efectivo y equivalentes de efectivo", parent_code="1"
        ),
        PCGEEntry(code="101", name="Caja", parent_code="10"),
        PCGEEntry(code="1011", name="Caja chica", parent_code="101"),
        PCGEEntry(code="102", name="Fondos fijos", parent_code="10"),
        PCGEEntry(code="11", name="Inversiones financieras", parent_code="1"),
        PCGEEntry(code="111", name="Inversiones negociables", parent_code="11"),
        PCGEEntry(code="2", name="Pasivo", parent_code=None),
        PCGEEntry(code="20", name="Mercaderías", parent_code="2"),
        PCGEEntry(code="201", name="Mercaderías manufacturadas", parent_code="20"),
    ]


@pytest.fixture
def catalog(sample_entries: list[PCGEEntry]) -> PCGECatalog:
    return PCGECatalog(sample_entries)


def test_empty_catalog():
    cat = PCGECatalog([])
    assert len(cat) == 0
    assert list(cat) == []
    assert "1" not in cat
    assert cat.get("1") is None
    with pytest.raises(KeyError):
        _ = cat["1"]
    assert cat.search("algo") == ()


def test_construction_from_list(sample_entries: list[PCGEEntry]):
    cat = PCGECatalog(sample_entries)
    assert len(cat) == len(sample_entries)


def test_construction_from_generator(sample_entries: list[PCGEEntry]):
    cat = PCGECatalog(entry for entry in sample_entries)
    assert len(cat) == len(sample_entries)


def test_preserves_order():
    e2 = PCGEEntry(code="2", name="Pasivo", parent_code=None)
    e1 = PCGEEntry(code="1", name="Activo", parent_code=None)
    cat = PCGECatalog([e2, e1])
    assert [e.code for e in cat] == ["2", "1"]


def test_len(catalog: PCGECatalog, sample_entries: list[PCGEEntry]):
    assert len(catalog) == len(sample_entries)


def test_iteration(catalog: PCGECatalog, sample_entries: list[PCGEEntry]):
    assert list(catalog) == sample_entries


def test_get_existing_and_non_existing(catalog: PCGECatalog):
    entry = catalog.get("10")
    assert entry is not None
    assert entry.code == "10"
    assert catalog.get("999") is None


def test_getitem_existing_and_non_existing(catalog: PCGECatalog):
    entry = catalog["10"]
    assert entry.code == "10"

    with pytest.raises(KeyError) as exc_info:
        _ = catalog["999"]
    assert exc_info.value.args[0] == "999"


def test_contains(catalog: PCGECatalog):
    assert "10" in catalog
    assert "1" in catalog
    assert "999" not in catalog


@pytest.mark.parametrize("invalid_key", [10, 10.5, None, ("10",)])
def test_get_and_getitem_reject_non_string(catalog: PCGECatalog, invalid_key):
    with pytest.raises(TypeError):
        catalog.get(invalid_key)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        _ = catalog[invalid_key]  # type: ignore[index]


def test_contains_non_string_returns_false(catalog: PCGECatalog):
    entry = catalog["10"]
    assert 10 not in catalog
    assert entry not in catalog
    assert None not in catalog
    assert ["10"] not in catalog


def test_non_existent_code(catalog: PCGECatalog):
    assert catalog.get("99999") is None
    with pytest.raises(KeyError) as exc_info:
        _ = catalog["99999"]
    assert exc_info.value.args[0] == "99999"


def test_construction_rejects_non_pcge_entry():
    with pytest.raises(TypeError):
        PCGECatalog(["not_a_pcge_entry"])  # type: ignore[list-item]

    with pytest.raises(TypeError):
        PCGECatalog([PCGEEntry(code="1", name="Activo"), 123])  # type: ignore[list-item]


def test_construction_rejects_duplicate_codes():
    root = PCGEEntry(code="1", name="Activo", parent_code=None)
    entry_a = PCGEEntry(code="10", name="Caja", parent_code="1")
    entry_b = PCGEEntry(code="10", name="Caja duplicada", parent_code="1")
    with pytest.raises(ValueError, match="Duplicate code"):
        PCGECatalog([root, entry_a, entry_b])

    same_entry = PCGEEntry(code="10", name="Caja", parent_code="1")
    with pytest.raises(ValueError, match="Duplicate code"):
        PCGECatalog([root, same_entry, same_entry])


def test_construction_rejects_missing_parent():
    with pytest.raises(ValueError, match="does not exist in catalog"):
        PCGECatalog([PCGEEntry(code="10", name="Cuenta", parent_code="9")])


def test_construction_rejects_direct_and_indirect_cycles():
    # Direct cycle: 10 <-> 20
    cycle_direct = [
        PCGEEntry(code="10", name="A", parent_code="20"),
        PCGEEntry(code="20", name="B", parent_code="10"),
    ]
    with pytest.raises(ValueError, match="Cycle detected"):
        PCGECatalog(cycle_direct)

    # Indirect cycle: 10 -> 20 -> 30 -> 10
    cycle_indirect = [
        PCGEEntry(code="10", name="A", parent_code="20"),
        PCGEEntry(code="20", name="B", parent_code="30"),
        PCGEEntry(code="30", name="C", parent_code="10"),
    ]
    with pytest.raises(ValueError, match="Cycle detected"):
        PCGECatalog(cycle_indirect)

    # Self cycle: 10 -> 10
    self_cycle = [
        PCGEEntry(code="10", name="A", parent_code="10"),
    ]
    with pytest.raises(ValueError, match="Cycle detected"):
        PCGECatalog(self_cycle)


def test_multiple_roots_allowed():
    roots = [
        PCGEEntry(code="1", name="Activo", parent_code=None),
        PCGEEntry(code="2", name="Pasivo", parent_code=None),
        PCGEEntry(code="3", name="Patrimonio", parent_code=None),
    ]
    cat = PCGECatalog(roots)
    assert len(cat) == 3
    assert cat.parent("1") is None
    assert cat.parent("2") is None
    assert cat.parent("3") is None


def test_construction_rejects_parent_not_matching_prefix():
    root = PCGEEntry(code="1", name="Activo", parent_code=None)
    child = PCGEEntry(code="99", name="Cuenta especial", parent_code="9")
    with pytest.raises(ValueError, match="does not exist in catalog"):
        PCGECatalog([root, child])

    root9 = PCGEEntry(code="9", name="Raíz 9", parent_code=None)
    child10 = PCGEEntry(code="10", name="Hijo 10 con padre 9", parent_code="9")
    with pytest.raises(ValueError, match="expected prefix"):
        PCGECatalog([root9, child10])


def test_construction_rejects_code_length_greater_than_six():
    e1 = PCGEEntry(code="6", name="Elemento", parent_code=None)
    e7 = PCGEEntry(code="6551111", name="Sintético 7 dígitos", parent_code="655111")
    with pytest.raises(ValueError, match="Invalid code length"):
        PCGECatalog([e1, e7])


def test_parent_of_root_is_none(catalog: PCGECatalog):
    assert catalog.parent("1") is None
    assert catalog.parent("2") is None


def test_parent_of_non_root(catalog: PCGECatalog):
    parent_10 = catalog.parent("10")
    assert parent_10 is not None
    assert parent_10.code == "1"

    parent_101 = catalog.parent("101")
    assert parent_101 is not None
    assert parent_101.code == "10"


def test_children_returns_direct_children_tuple(catalog: PCGECatalog):
    children_1 = catalog.children("1")
    assert isinstance(children_1, tuple)
    assert [c.code for c in children_1] == ["10", "11"]

    children_10 = catalog.children("10")
    assert isinstance(children_10, tuple)
    assert [c.code for c in children_10] == ["101", "102"]


def test_children_of_leaf_returns_empty_tuple(catalog: PCGECatalog):
    children_1011 = catalog.children("1011")
    assert isinstance(children_1011, tuple)
    assert children_1011 == ()


def test_ancestors_order_from_immediate_parent_to_root(catalog: PCGECatalog):
    anc_1011 = catalog.ancestors("1011")
    assert isinstance(anc_1011, tuple)
    assert [a.code for a in anc_1011] == ["101", "10", "1"]

    anc_root = catalog.ancestors("1")
    assert isinstance(anc_root, tuple)
    assert anc_root == ()


def test_descendants_depth_first_pre_order(catalog: PCGECatalog):
    desc_1 = catalog.descendants("1")
    assert isinstance(desc_1, tuple)
    assert [d.code for d in desc_1] == ["10", "101", "1011", "102", "11", "111"]

    assert catalog.descendants("1011") == ()


@pytest.mark.parametrize(
    "method_name", ["parent", "children", "ancestors", "descendants"]
)
def test_navigation_methods_raise_key_error_for_non_existent_code(
    catalog: PCGECatalog, method_name: str
):
    method = getattr(catalog, method_name)
    with pytest.raises(KeyError) as exc_info:
        method("99999")
    assert exc_info.value.args[0] == "99999"


@pytest.mark.parametrize(
    "method_name", ["parent", "children", "ancestors", "descendants"]
)
@pytest.mark.parametrize("invalid_arg", [10, None, ("10",), True])
def test_navigation_methods_raise_type_error_for_non_string(
    catalog: PCGECatalog, method_name: str, invalid_arg
):
    method = getattr(catalog, method_name)
    with pytest.raises(TypeError):
        method(invalid_arg)


def test_navigation_methods_reject_pcge_entry_as_argument(catalog: PCGECatalog):
    entry = catalog["10"]
    for method in (
        catalog.parent,
        catalog.children,
        catalog.ancestors,
        catalog.descendants,
    ):
        with pytest.raises(TypeError):
            method(entry)  # type: ignore[arg-type]


def test_search_by_code(catalog: PCGECatalog):
    results = catalog.search("201")
    assert isinstance(results, tuple)
    assert [e.code for e in results] == ["201"]

    results_multiple = catalog.search("10")
    assert [e.code for e in results_multiple] == ["10", "101", "1011", "102"]


def test_search_by_name_substring(catalog: PCGECatalog):
    results = catalog.search("financ")
    assert [e.code for e in results] == ["11"]
    assert results[0].name == "Inversiones financieras"


def test_search_case_insensitive(catalog: PCGECatalog):
    results = catalog.search("EFECTIVO")
    assert [e.code for e in results] == ["10"]

    results_lower = catalog.search("caja chica")
    assert [e.code for e in results_lower] == ["1011"]


def test_search_diacritic_insensitive(catalog: PCGECatalog):
    results1 = catalog.search("mercaderias")
    assert [e.code for e in results1] == ["20", "201"]

    results2 = catalog.search("Mercaderías")
    assert [e.code for e in results2] == ["20", "201"]


def test_search_preserves_catalog_order(catalog: PCGECatalog):
    results = catalog.search("1")
    assert [e.code for e in results] == [
        "1",
        "10",
        "101",
        "1011",
        "102",
        "11",
        "111",
        "201",
    ]


def test_search_no_results_returns_empty_tuple(catalog: PCGECatalog):
    results = catalog.search("palabra_inexistente_xyz")
    assert isinstance(results, tuple)
    assert results == ()


def test_search_empty_or_whitespace_query_raises_value_error(catalog: PCGECatalog):
    with pytest.raises(ValueError):
        catalog.search("")

    with pytest.raises(ValueError):
        catalog.search("   ")

    with pytest.raises(ValueError):
        catalog.search("\t\n")


@pytest.mark.parametrize("invalid_query", [123, None, ["caja"], True])
def test_search_invalid_type_raises_type_error(catalog: PCGECatalog, invalid_query):
    with pytest.raises(TypeError):
        catalog.search(invalid_query)  # type: ignore[arg-type]


def test_search_entry_matching_both_code_and_name_appears_once():
    cat = PCGECatalog(
        [
            PCGEEntry(code="1", name="Elemento 1 activo", parent_code=None),
        ]
    )
    results = cat.search("1")
    assert len(results) == 1
    assert results[0].code == "1"


def test_pcge_catalog_public_export():
    from pcge import PCGECatalog as ExportedCatalog

    assert ExportedCatalog is PCGECatalog


def test_catalog_manual_without_metadata(catalog: PCGECatalog):
    assert catalog.metadata is None


def test_catalog_with_valid_metadata(sample_entries: list[PCGEEntry]):
    meta = PCGEMetadata(
        pcge_version="2026",
        schema_version=1,
        dataset_revision=1,
        entry_count=len(sample_entries),
    )
    cat = PCGECatalog(sample_entries, metadata=meta)
    assert cat.metadata == meta
    assert cat.metadata is meta


def test_catalog_rejects_invalid_metadata_type(sample_entries: list[PCGEEntry]):
    with pytest.raises(TypeError):
        PCGECatalog(sample_entries, metadata="not_metadata")  # type: ignore[arg-type]


def test_catalog_rejects_inconsistent_entry_count(sample_entries: list[PCGEEntry]):
    meta = PCGEMetadata(
        pcge_version="2026",
        schema_version=1,
        dataset_revision=1,
        entry_count=len(sample_entries) + 5,
    )
    with pytest.raises(ValueError, match="metadata.entry_count"):
        PCGECatalog(sample_entries, metadata=meta)


def test_catalog_rejects_positional_metadata(sample_entries: list[PCGEEntry]):
    meta = PCGEMetadata(
        pcge_version="2026",
        schema_version=1,
        dataset_revision=1,
        entry_count=len(sample_entries),
    )
    with pytest.raises(TypeError):
        PCGECatalog(sample_entries, meta)  # type: ignore[misc]


@pytest.fixture
def synthetic_hierarchy_1_to_6() -> list[PCGEEntry]:
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


def test_catalog_generator_consumed_once(
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
    cat = PCGECatalog(gen(), metadata=meta)
    assert len(cat) == len(synthetic_hierarchy_1_to_6)
    assert consumed_count == len(synthetic_hierarchy_1_to_6)


def test_catalog_six_digit_official_code_without_sixth_pcge_level(
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
    cat = PCGECatalog(synthetic_hierarchy_1_to_6, metadata=meta)
    assert cat["655111"].code == "655111"
    assert cat["655111"].code_length == 6
    assert cat["655111"].pcge_level is None
