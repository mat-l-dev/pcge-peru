import unicodedata
from collections.abc import Iterable, Iterator

from pcge.metadata import PCGEMetadata
from pcge.models import PCGEEntry


def _normalize_for_search(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


class PCGECatalog:
    def __init__(
        self,
        entries: Iterable[PCGEEntry],
        *,
        metadata: PCGEMetadata | None = None,
    ) -> None:
        entries_list: list[PCGEEntry] = []
        entries_by_code: dict[str, PCGEEntry] = {}
        children_by_code: dict[str, list[PCGEEntry]] = {}

        for item in entries:
            if not isinstance(item, PCGEEntry):
                item_type = type(item).__name__
                raise TypeError(
                    f"All elements must be PCGEEntry instances, got {item_type}"
                )
            if item.code in entries_by_code:
                raise ValueError(f"Duplicate code found: '{item.code}'")
            entries_list.append(item)
            entries_by_code[item.code] = item
            children_by_code[item.code] = []

        if metadata is not None:
            if not isinstance(metadata, PCGEMetadata):
                item_type = type(metadata).__name__
                raise TypeError(
                    f"metadata must be PCGEMetadata or None, got {item_type}"
                )
            if metadata.entry_count != len(entries_list):
                raise ValueError(
                    f"metadata.entry_count ({metadata.entry_count}) does not match "
                    f"catalog entry count ({len(entries_list)})"
                )

        for entry in entries_list:
            if entry.parent_code is not None:
                if entry.parent_code not in entries_by_code:
                    raise ValueError(
                        f"Parent code '{entry.parent_code}' for code '{entry.code}' "
                        "does not exist in catalog"
                    )
                children_by_code[entry.parent_code].append(entry)

        visited_status: dict[str, int] = {}
        for code in entries_by_code:
            if visited_status.get(code) == 2:
                continue
            curr: str | None = code
            chain: list[str] = []
            chain_set: set[str] = set()
            while curr is not None:
                if visited_status.get(curr) == 2:
                    break
                if curr in chain_set:
                    raise ValueError(f"Cycle detected involving code '{curr}'")
                chain.append(curr)
                chain_set.add(curr)
                curr = entries_by_code[curr].parent_code
            for c in chain:
                visited_status[c] = 2

        self._metadata: PCGEMetadata | None = metadata
        self._entries: dict[str, PCGEEntry] = entries_by_code
        self._entries_order: tuple[PCGEEntry, ...] = tuple(entries_list)
        self._children: dict[str, tuple[PCGEEntry, ...]] = {
            code: tuple(kids) for code, kids in children_by_code.items()
        }

    @property
    def metadata(self) -> PCGEMetadata | None:
        return self._metadata

    def __len__(self) -> int:
        return len(self._entries_order)

    def __iter__(self) -> Iterator[PCGEEntry]:
        return iter(self._entries_order)

    def __contains__(self, item: object) -> bool:
        if not isinstance(item, str):
            return False
        return item in self._entries

    def __getitem__(self, code: str) -> PCGEEntry:
        if not isinstance(code, str):
            raise TypeError(f"code must be a str, got {type(code).__name__}")
        try:
            return self._entries[code]
        except KeyError:
            raise KeyError(code) from None

    def get(self, code: str) -> PCGEEntry | None:
        if not isinstance(code, str):
            raise TypeError(f"code must be a str, got {type(code).__name__}")
        return self._entries.get(code)

    def _require_code(self, code: str) -> PCGEEntry:
        if not isinstance(code, str):
            raise TypeError(f"code must be a str, got {type(code).__name__}")
        try:
            return self._entries[code]
        except KeyError:
            raise KeyError(code) from None

    def parent(self, code: str) -> PCGEEntry | None:
        entry = self._require_code(code)
        if entry.parent_code is None:
            return None
        return self._entries[entry.parent_code]

    def children(self, code: str) -> tuple[PCGEEntry, ...]:
        self._require_code(code)
        return self._children[code]

    def ancestors(self, code: str) -> tuple[PCGEEntry, ...]:
        entry = self._require_code(code)
        ancestors: list[PCGEEntry] = []
        curr_parent = entry.parent_code
        while curr_parent is not None:
            parent_entry = self._entries[curr_parent]
            ancestors.append(parent_entry)
            curr_parent = parent_entry.parent_code
        return tuple(ancestors)

    def descendants(self, code: str) -> tuple[PCGEEntry, ...]:
        self._require_code(code)
        direct_children = self._children[code]
        if not direct_children:
            return ()

        result: list[PCGEEntry] = []
        stack: list[PCGEEntry] = list(reversed(direct_children))
        while stack:
            curr_entry = stack.pop()
            result.append(curr_entry)
            kids = self._children[curr_entry.code]
            if kids:
                stack.extend(reversed(kids))

        return tuple(result)

    def search(self, query: str) -> tuple[PCGEEntry, ...]:
        if not isinstance(query, str):
            raise TypeError(f"query must be a str, got {type(query).__name__}")
        cleaned = query.strip()
        if not cleaned:
            raise ValueError("query cannot be empty or whitespace only")

        norm_query = _normalize_for_search(cleaned)
        matches: list[PCGEEntry] = []
        for entry in self._entries_order:
            norm_code = _normalize_for_search(entry.code)
            norm_name = _normalize_for_search(entry.name)
            if norm_query in norm_code or norm_query in norm_name:
                matches.append(entry)
        return tuple(matches)
