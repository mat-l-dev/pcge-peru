from dataclasses import dataclass

from pcge.enums import PCGELevel


@dataclass(frozen=True, slots=True)
class PCGEEntry:
    code: str
    name: str
    parent_code: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, str):
            raise TypeError("code must be a str")
        if not self.code:
            raise ValueError("code cannot be empty")
        if not (self.code.isascii() and self.code.isdigit()):
            raise ValueError("code must contain only ASCII digits 0-9")

        if not isinstance(self.name, str):
            raise TypeError("name must be a str")
        if not self.name.strip():
            raise ValueError("name cannot be empty or whitespace only")

        if self.parent_code is not None:
            if not isinstance(self.parent_code, str):
                raise TypeError("parent_code must be a str or None")
            if not self.parent_code:
                raise ValueError("parent_code cannot be empty")
            if not (self.parent_code.isascii() and self.parent_code.isdigit()):
                raise ValueError("parent_code must contain only ASCII digits 0-9")

        if self.code_length == 1 and self.parent_code is not None:
            raise ValueError("Root code (length 1) must have parent_code=None")
        if self.code_length > 1 and self.parent_code is None:
            raise ValueError("Non-root code (length > 1) must have a parent_code")

    @property
    def code_length(self) -> int:
        return len(self.code)

    @property
    def pcge_level(self) -> PCGELevel | None:
        levels = {
            1: PCGELevel.ELEMENT,
            2: PCGELevel.ACCOUNT,
            3: PCGELevel.SUBACCOUNT,
            4: PCGELevel.DIVISIONARY,
            5: PCGELevel.SUBDIVISIONARY,
        }
        return levels.get(self.code_length)
