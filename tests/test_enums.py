from pcge.enums import PCGELevel


def test_pcge_levels_have_expected_values():
    assert PCGELevel.ELEMENT == "element"
    assert PCGELevel.ACCOUNT == "account"
    assert PCGELevel.SUBACCOUNT == "subaccount"
    assert PCGELevel.DIVISIONARY == "divisionary"
    assert PCGELevel.SUBDIVISIONARY == "subdivisionary"


def test_pcge_level_has_exactly_five_members_and_no_sixth_level():
    expected_members = [
        "ELEMENT",
        "ACCOUNT",
        "SUBACCOUNT",
        "DIVISIONARY",
        "SUBDIVISIONARY",
    ]
    assert [member.name for member in PCGELevel] == expected_members
    assert len(PCGELevel) == 5
    assert not hasattr(PCGELevel, "SIXTH_LEVEL")
