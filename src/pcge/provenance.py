import re
from dataclasses import dataclass
from datetime import date

_SHA256_RE = re.compile(r"^[0-9A-F]{64}\Z")


def _validate_str_non_empty(val: str, field_name: str) -> None:
    if not isinstance(val, str):
        raise TypeError(f"{field_name} must be a str")
    if not val.strip():
        raise ValueError(f"{field_name} cannot be empty or whitespace only")


def _validate_date(val: date, field_name: str) -> None:
    if type(val) is not date:
        raise TypeError(f"{field_name} must be a datetime.date instance")


def _validate_sha256(val: str, field_name: str) -> None:
    if not isinstance(val, str):
        raise TypeError(f"{field_name} must be a str")
    if not _SHA256_RE.match(val):
        raise ValueError(
            f"{field_name} must be exactly 64 uppercase hex characters [0-9A-F]"
        )


def _validate_page_range(val: tuple[int, int], field_name: str) -> None:
    if not isinstance(val, tuple):
        raise TypeError(f"{field_name} must be a tuple[int, int]")
    if len(val) != 2:
        raise ValueError(f"{field_name} must contain exactly 2 elements (first, last)")
    first, last = val
    if isinstance(first, bool) or not isinstance(first, int):
        raise TypeError(f"{field_name}[0] must be an int")
    if isinstance(last, bool) or not isinstance(last, int):
        raise TypeError(f"{field_name}[1] must be an int")
    if first < 1:
        raise ValueError(f"{field_name}[0] must be >= 1")
    if last < 1:
        raise ValueError(f"{field_name}[1] must be >= 1")
    if first > last:
        raise ValueError(
            f"{field_name} first page ({first}) cannot be greater than "
            f"last page ({last})"
        )


@dataclass(frozen=True, slots=True)
class PCGEProvenance:
    title: str
    authority: str
    resolution: str
    resolution_date: date
    publication_date: date
    mandatory_effective_date: date
    resolution_url: str
    source_filename: str
    source_sha256: str
    catalog_chapter: str
    catalog_pdf_pages: tuple[int, int]
    catalog_printed_pages: tuple[int, int]
    dataset_sha256: str

    def __post_init__(self) -> None:
        _validate_str_non_empty(self.title, "title")
        _validate_str_non_empty(self.authority, "authority")
        _validate_str_non_empty(self.resolution, "resolution")
        _validate_date(self.resolution_date, "resolution_date")
        _validate_date(self.publication_date, "publication_date")
        _validate_date(self.mandatory_effective_date, "mandatory_effective_date")
        _validate_str_non_empty(self.resolution_url, "resolution_url")
        _validate_str_non_empty(self.source_filename, "source_filename")
        _validate_sha256(self.source_sha256, "source_sha256")
        _validate_str_non_empty(self.catalog_chapter, "catalog_chapter")
        _validate_page_range(self.catalog_pdf_pages, "catalog_pdf_pages")
        _validate_page_range(self.catalog_printed_pages, "catalog_printed_pages")
        _validate_sha256(self.dataset_sha256, "dataset_sha256")
