from datetime import date, datetime

import pytest

from pcge.provenance import PCGEProvenance


def _make_valid_provenance(**kwargs):
    defaults = {
        "title": "Plan Contable General Empresarial Modificado 2019",
        "authority": "Consejo Normativo de Contabilidad",
        "resolution": "Resolución N.° 002-2019-EF/30",
        "resolution_date": date(2019, 5, 16),
        "publication_date": date(2019, 5, 24),
        "mandatory_effective_date": date(2020, 1, 1),
        "resolution_url": "https://busquedas.elperuano.pe/dispositivo/NL/1772236-1",
        "source_filename": "PCGE_2019.pdf",
        "source_sha256": (
            "EC0CA9D36CD2F5CDB6D14ECB45A6E510879DF929372FDB033BC2DF88329EB9F2"
        ),
        "catalog_chapter": "Capítulo II",
        "catalog_pdf_pages": (21, 62),
        "catalog_printed_pages": (20, 61),
        "dataset_sha256": (
            "FC70E43B94D0718373AB3B9F81202731E5295EDEDF0DF75231A2FFB3C2BEEC04"
        ),
    }
    defaults.update(kwargs)
    return PCGEProvenance(**defaults)


def test_provenance_valid_construction():
    prov = _make_valid_provenance()
    assert prov.title == "Plan Contable General Empresarial Modificado 2019"
    assert prov.resolution_date == date(2019, 5, 16)
    assert prov.catalog_pdf_pages == (21, 62)
    assert (
        prov.dataset_sha256
        == "FC70E43B94D0718373AB3B9F81202731E5295EDEDF0DF75231A2FFB3C2BEEC04"
    )


def test_provenance_frozen():
    prov = _make_valid_provenance()
    with pytest.raises((AttributeError, TypeError)):
        prov.title = "Nuevo titulo"  # type: ignore[misc]


def test_provenance_rejects_datetime_for_date():
    dt = datetime(2019, 5, 16, 12, 0, 0)
    with pytest.raises(TypeError, match="resolution_date"):
        _make_valid_provenance(resolution_date=dt)
    with pytest.raises(TypeError, match="publication_date"):
        _make_valid_provenance(publication_date=dt)
    with pytest.raises(TypeError, match="mandatory_effective_date"):
        _make_valid_provenance(mandatory_effective_date=dt)


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
@pytest.mark.parametrize("invalid_val", ["", "   ", "\t\n"])
def test_provenance_rejects_empty_or_whitespace_strings(field, invalid_val):
    with pytest.raises(ValueError, match=field):
        _make_valid_provenance(**{field: invalid_val})


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
def test_provenance_rejects_non_string_types(field):
    with pytest.raises(TypeError, match=field):
        _make_valid_provenance(**{field: 123})


@pytest.mark.parametrize("hash_field", ["source_sha256", "dataset_sha256"])
@pytest.mark.parametrize(
    "invalid_hash, match_word",
    [
        (
            "ec0ca9d36cd2f5cdb6d14ecb45a6e510879df929372fdb033bc2df88329eb9f2",
            "uppercase",
        ),  # lowercase
        ("EC0CA9D36CD2", "64"),  # too short
        (
            "EC0CA9D36CD2F5CDB6D14ECB45A6E510879DF929372FDB033BC2DF88329EB9F2AA",
            "64",
        ),  # too long
        (
            "EC0CA9D36CD2F5CDB6D14ECB45A6E510879DF929372FDB033BC2DF88329EB9FZ",
            "uppercase",
        ),  # non-hex char Z
    ],
)
def test_provenance_rejects_invalid_sha256(hash_field, invalid_hash, match_word):
    with pytest.raises(ValueError, match=match_word):
        _make_valid_provenance(**{hash_field: invalid_hash})


@pytest.mark.parametrize("hash_field", ["source_sha256", "dataset_sha256"])
def test_provenance_rejects_non_str_sha256(hash_field):
    with pytest.raises(TypeError, match=hash_field):
        _make_valid_provenance(**{hash_field: 12345})


@pytest.mark.parametrize("page_field", ["catalog_pdf_pages", "catalog_printed_pages"])
@pytest.mark.parametrize(
    "invalid_range, exc, match_text",
    [
        ([21, 62], TypeError, "tuple"),  # list instead of tuple
        ((21,), ValueError, "2 elements"),  # 1 element
        ((21, 30, 40), ValueError, "2 elements"),  # 3 elements
        ((True, 62), TypeError, "int"),  # bool instead of int
        ((21, False), TypeError, "int"),  # bool instead of int
        ((0, 62), ValueError, ">= 1"),  # 0
        ((-5, 62), ValueError, ">= 1"),  # negative
        ((21, 0), ValueError, ">= 1"),  # last 0
        ((62, 21), ValueError, "cannot be greater"),  # first > last
    ],
)
def test_provenance_rejects_invalid_page_ranges(
    page_field, invalid_range, exc, match_text
):
    with pytest.raises(exc, match=match_text):
        _make_valid_provenance(**{page_field: invalid_range})
