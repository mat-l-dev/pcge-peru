from dataclasses import FrozenInstanceError

import pytest

from pcge.enums import PCGELevel
from pcge.models import PCGEEntry


def test_pcge_entry_creation():
    entry = PCGEEntry(code="20111", name="Costo", parent_code="2011")

    assert entry.code == "20111"
    assert entry.name == "Costo"
    assert entry.parent_code == "2011"


def test_code_length_is_derived_from_code():
    entry = PCGEEntry(code="20111", name="Costo", parent_code="2011")

    assert entry.code_length == 5


@pytest.mark.parametrize(
    ("code", "parent_code", "expected_level"),
    [
        ("1", None, PCGELevel.ELEMENT),
        ("10", "1", PCGELevel.ACCOUNT),
        ("101", "10", PCGELevel.SUBACCOUNT),
        ("1011", "101", PCGELevel.DIVISIONARY),
        ("10111", "1011", PCGELevel.SUBDIVISIONARY),
    ],
)
def test_formal_pcge_levels_derived_from_code_length(
    code: str, parent_code: str | None, expected_level: PCGELevel
):
    entry = PCGEEntry(code=code, name="Elemento o cuenta", parent_code=parent_code)

    assert entry.code_length == len(code)
    assert entry.pcge_level == expected_level


def test_six_digit_official_entry_has_no_formal_pcge_level():
    entry = PCGEEntry(
        code="655111",
        name="Operacion",
        parent_code="65511",
    )

    assert entry.code_length == 6
    assert entry.pcge_level is None


def test_name_preserves_original_value_without_normalization():
    raw_name = "  Mercaderías manufacturadas \t "
    entry = PCGEEntry(code="20", name=raw_name, parent_code="2")

    assert entry.name == raw_name


@pytest.mark.parametrize("invalid_code", [123, None, ("1",)])
def test_code_invalid_type_raises_type_error(invalid_code):
    with pytest.raises(TypeError):
        PCGEEntry(code=invalid_code, name="Activo", parent_code=None)


def test_code_empty_raises_value_error():
    with pytest.raises(ValueError):
        PCGEEntry(code="", name="Activo", parent_code=None)


@pytest.mark.parametrize("invalid_code", ["10A", "1-0", "1 0", "10.1"])
def test_code_with_non_numeric_characters_raises_value_error(invalid_code):
    with pytest.raises(ValueError):
        PCGEEntry(code=invalid_code, name="Cuenta", parent_code="1")


@pytest.mark.parametrize("invalid_code", ["１０", "١٠", "²"])
def test_code_with_unicode_non_ascii_digits_raises_value_error(invalid_code):
    with pytest.raises(ValueError):
        PCGEEntry(code=invalid_code, name="Cuenta", parent_code="1")


@pytest.mark.parametrize("invalid_name", [123, None, []])
def test_name_invalid_type_raises_type_error(invalid_name):
    with pytest.raises(TypeError):
        PCGEEntry(code="1", name=invalid_name, parent_code=None)


@pytest.mark.parametrize("invalid_name", ["", "   ", "\t \n "])
def test_name_empty_or_whitespace_only_raises_value_error(invalid_name):
    with pytest.raises(ValueError):
        PCGEEntry(code="1", name=invalid_name, parent_code=None)


@pytest.mark.parametrize("invalid_parent", [1, True, ["1"]])
def test_parent_code_invalid_type_raises_type_error(invalid_parent):
    with pytest.raises(TypeError):
        PCGEEntry(code="10", name="Cuenta", parent_code=invalid_parent)


def test_parent_code_empty_raises_value_error():
    with pytest.raises(ValueError):
        PCGEEntry(code="10", name="Cuenta", parent_code="")


@pytest.mark.parametrize("invalid_parent", ["1A", "1-0", "1 0"])
def test_parent_code_with_non_numeric_characters_raises_value_error(invalid_parent):
    with pytest.raises(ValueError):
        PCGEEntry(code="10", name="Cuenta", parent_code=invalid_parent)


@pytest.mark.parametrize("invalid_parent", ["１", "١", "²"])
def test_parent_code_with_unicode_non_ascii_digits_raises_value_error(invalid_parent):
    with pytest.raises(ValueError):
        PCGEEntry(code="10", name="Cuenta", parent_code=invalid_parent)


def test_root_code_with_parent_raises_value_error():
    with pytest.raises(ValueError):
        PCGEEntry(code="1", name="Activo", parent_code="0")


def test_non_root_code_without_parent_raises_value_error():
    with pytest.raises(ValueError):
        PCGEEntry(code="10", name="Cuenta", parent_code=None)

    with pytest.raises(ValueError):
        PCGEEntry(code="10", name="Cuenta")


def test_pcge_entry_is_immutable():
    entry = PCGEEntry(code="10", name="Cuenta", parent_code="1")

    with pytest.raises(FrozenInstanceError):
        entry.code = "20"

    with pytest.raises(FrozenInstanceError):
        entry.name = "Otro"

    with pytest.raises(FrozenInstanceError):
        entry.parent_code = "2"


def test_pcge_entry_has_slots_and_no_dict():
    entry = PCGEEntry(code="10", name="Cuenta", parent_code="1")

    assert not hasattr(entry, "__dict__")
    assert hasattr(entry, "__slots__")
    assert tuple(PCGEEntry.__slots__) == ("code", "name", "parent_code")


def test_pcge_entry_equality_by_value():
    entry1 = PCGEEntry(code="10", name="Cuenta", parent_code="1")
    entry2 = PCGEEntry(code="10", name="Cuenta", parent_code="1")

    assert entry1 == entry2


def test_pcge_entry_hash_and_usable_in_sets_and_mappings():
    entry1 = PCGEEntry(code="10", name="Cuenta", parent_code="1")
    entry2 = PCGEEntry(code="10", name="Cuenta", parent_code="1")

    assert hash(entry1) == hash(entry2)
    assert len({entry1, entry2}) == 1

    mapping = {entry1: "primary"}
    assert mapping[entry2] == "primary"


def test_pcge_entry_inequality_on_different_fields():
    base = PCGEEntry(code="10", name="Cuenta", parent_code="1")
    different_code = PCGEEntry(code="20", name="Cuenta", parent_code="1")
    different_name = PCGEEntry(code="10", name="Inversiones", parent_code="1")
    different_parent = PCGEEntry(code="10", name="Cuenta", parent_code="2")

    assert base != different_code
    assert base != different_name
    assert base != different_parent


def test_pcge_entry_allows_locally_unmatched_numeric_parent_code():
    entry = PCGEEntry(code="10", name="Cuenta", parent_code="9999")

    assert entry.code == "10"
    assert entry.parent_code == "9999"
