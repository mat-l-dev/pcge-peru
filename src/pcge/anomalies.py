from dataclasses import dataclass


def _validate_pos_int(val: int, field_name: str) -> None:
    if isinstance(val, bool) or not isinstance(val, int):
        raise TypeError(f"{field_name} must be an int")
    if val < 1:
        raise ValueError(f"{field_name} must be >= 1")


def _validate_str_non_whitespace(val: str, field_name: str) -> None:
    if not isinstance(val, str):
        raise TypeError(f"{field_name} must be a str")
    if not val.strip():
        raise ValueError(f"{field_name} cannot be empty or whitespace only")


@dataclass(frozen=True, slots=True)
class PCGEAnomalyOccurrence:
    occurrence_index: int
    pdf_page: int
    printed_page: int
    printed_code: str
    printed_name: str
    printed_parent_code: str
    disposition: str

    def __post_init__(self) -> None:
        _validate_pos_int(self.occurrence_index, "occurrence_index")
        _validate_pos_int(self.pdf_page, "pdf_page")
        _validate_pos_int(self.printed_page, "printed_page")
        _validate_str_non_whitespace(self.printed_code, "printed_code")
        _validate_str_non_whitespace(self.printed_name, "printed_name")
        _validate_str_non_whitespace(self.printed_parent_code, "printed_parent_code")
        _validate_str_non_whitespace(self.disposition, "disposition")


@dataclass(frozen=True, slots=True)
class PCGEAnomaly:
    id: str
    type: str
    codes: tuple[str, ...]
    status: str
    description: str
    decision: str
    confirmation_no_invented_code: str
    occurrences: tuple[PCGEAnomalyOccurrence, ...]

    def __post_init__(self) -> None:
        _validate_str_non_whitespace(self.id, "id")
        _validate_str_non_whitespace(self.type, "type")
        _validate_str_non_whitespace(self.status, "status")
        _validate_str_non_whitespace(self.description, "description")
        _validate_str_non_whitespace(self.decision, "decision")
        _validate_str_non_whitespace(
            self.confirmation_no_invented_code, "confirmation_no_invented_code"
        )

        if not isinstance(self.codes, tuple):
            raise TypeError("codes must be a tuple[str, ...]")
        if not self.codes:
            raise ValueError("codes tuple cannot be empty")
        seen_codes: set[str] = set()
        for i, c in enumerate(self.codes):
            if not isinstance(c, str):
                raise TypeError(f"codes[{i}] must be a str, got {type(c).__name__}")
            if not c:
                raise ValueError(f"codes[{i}] cannot be empty")
            if not c.strip():
                raise ValueError(f"codes[{i}] cannot be whitespace only")
            if c in seen_codes:
                raise ValueError(f"Duplicate code {c!r} in codes tuple")
            seen_codes.add(c)

        if not isinstance(self.occurrences, tuple):
            raise TypeError("occurrences must be a tuple[PCGEAnomalyOccurrence, ...]")
        if not self.occurrences:
            raise ValueError("occurrences tuple cannot be empty")
        seen_indices: set[int] = set()
        for i, occ in enumerate(self.occurrences):
            if not isinstance(occ, PCGEAnomalyOccurrence):
                raise TypeError(
                    f"occurrences[{i}] must be a PCGEAnomalyOccurrence instance, "
                    f"got {type(occ).__name__}"
                )
            if occ.occurrence_index in seen_indices:
                raise ValueError(
                    f"Duplicate occurrence_index {occ.occurrence_index} in occurrences"
                )
            seen_indices.add(occ.occurrence_index)
