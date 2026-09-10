import importlib.resources as importlib_resources
import json
from typing import Any

from pcge.catalog import PCGECatalog
from pcge.exceptions import PCGEDataError
from pcge.metadata import PCGEMetadata
from pcge.models import PCGEEntry


class _DuplicateJSONKeyError(ValueError):
    def __init__(self, key: str) -> None:
        super().__init__(f"Duplicate JSON key: {key!r}")
        self.key = key


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJSONKeyError(key)
        result[key] = value
    return result


def _loads_json_strict(text: str, filename: str, version: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except _DuplicateJSONKeyError as err:
        raise PCGEDataError(
            f"Duplicate JSON key '{err.key}' in '{filename}' for version '{version}'"
        ) from err
    except json.JSONDecodeError as err:
        raise PCGEDataError(
            f"Malformed JSON in '{filename}' for version '{version}': {err}"
        ) from err


_SUPPORTED_VERSIONS: tuple[str, ...] = ("2019", "2026")


def available_versions() -> tuple[str, ...]:
    return _SUPPORTED_VERSIONS


def load_catalog(version: str) -> PCGECatalog:
    if not isinstance(version, str):
        item_type = type(version).__name__
        raise TypeError(f"version must be a str, got {item_type}")
    if not version:
        raise PCGEDataError("version cannot be empty")
    if not (version.isascii() and version.isdigit()):
        raise PCGEDataError(f"version must contain only ASCII digits, got {version!r}")
    if version not in _SUPPORTED_VERSIONS:
        available = ", ".join(_SUPPORTED_VERSIONS)
        raise PCGEDataError(
            f"Version '{version}' is not available. Available versions: {available}"
        )

    try:
        data_pkg = importlib_resources.files("pcge.data")
    except Exception as err:
        raise PCGEDataError(
            f"Unable to locate resource package 'pcge.data': {err}"
        ) from err

    version_dir = data_pkg.joinpath(version)
    metadata_path = version_dir.joinpath("metadata.json")
    entries_path = version_dir.joinpath("entries.json")

    try:
        metadata_text = metadata_path.read_text(encoding="utf-8")
    except FileNotFoundError as err:
        raise PCGEDataError(
            f"Version '{version}' is not available: 'metadata.json' not found"
        ) from err
    except OSError as err:
        raise PCGEDataError(
            f"Failed to read 'metadata.json' for version '{version}': {err}"
        ) from err
    except UnicodeDecodeError as err:
        raise PCGEDataError(
            f"Failed to decode 'metadata.json' as UTF-8 for version '{version}': {err}"
        ) from err

    try:
        entries_text = entries_path.read_text(encoding="utf-8")
    except FileNotFoundError as err:
        raise PCGEDataError(
            f"Version '{version}' is not available: 'entries.json' not found"
        ) from err
    except OSError as err:
        raise PCGEDataError(
            f"Failed to read 'entries.json' for version '{version}': {err}"
        ) from err
    except UnicodeDecodeError as err:
        raise PCGEDataError(
            f"Failed to decode 'entries.json' as UTF-8 for version '{version}': {err}"
        ) from err

    raw_metadata = _loads_json_strict(metadata_text, "metadata.json", version)

    if not isinstance(raw_metadata, dict):
        raise PCGEDataError(
            f"metadata.json for version '{version}' must contain a JSON object"
        )

    required_meta_keys = {
        "pcge_version",
        "schema_version",
        "dataset_revision",
        "entry_count",
    }
    missing_meta = required_meta_keys - set(raw_metadata.keys())
    if missing_meta:
        raise PCGEDataError(
            f"metadata.json for version '{version}' missing required keys: "
            f"{sorted(missing_meta)}"
        )
    extra_meta = set(raw_metadata.keys()) - required_meta_keys
    if extra_meta:
        raise PCGEDataError(
            f"metadata.json for version '{version}' has unexpected extra keys: "
            f"{sorted(extra_meta)}"
        )

    if not isinstance(raw_metadata["pcge_version"], str):
        raise PCGEDataError(
            f"metadata.json for version '{version}': 'pcge_version' must be a str"
        )
    if raw_metadata["pcge_version"] != version:
        raise PCGEDataError(
            f"metadata.json pcge_version '{raw_metadata['pcge_version']}' "
            f"does not match requested version '{version}'"
        )

    for int_field in ("schema_version", "dataset_revision", "entry_count"):
        val = raw_metadata[int_field]
        if isinstance(val, bool) or not isinstance(val, int):
            val_type = type(val).__name__
            raise PCGEDataError(
                f"metadata.json for version '{version}': '{int_field}' "
                f"must be an integer, got {val_type}"
            )

    try:
        metadata = PCGEMetadata(
            pcge_version=raw_metadata["pcge_version"],
            schema_version=raw_metadata["schema_version"],
            dataset_revision=raw_metadata["dataset_revision"],
            entry_count=raw_metadata["entry_count"],
        )
    except (TypeError, ValueError) as err:
        raise PCGEDataError(
            f"Invalid metadata in 'metadata.json' for version '{version}': {err}"
        ) from err

    if metadata.schema_version != 1:
        raise PCGEDataError(
            f"Unsupported schema_version: {metadata.schema_version}, expected 1"
        )

    raw_entries = _loads_json_strict(entries_text, "entries.json", version)

    if not isinstance(raw_entries, list):
        raise PCGEDataError(
            f"entries.json for version '{version}' must contain a JSON array"
        )

    required_entry_keys = {"code", "name", "parent_code"}
    entries_list: list[PCGEEntry] = []
    for idx, item in enumerate(raw_entries):
        if not isinstance(item, dict):
            raise PCGEDataError(
                f"entries.json for version '{version}' at index {idx} "
                "must be a JSON object"
            )
        missing_entry_keys = required_entry_keys - set(item.keys())
        if missing_entry_keys:
            raise PCGEDataError(
                f"entries.json for version '{version}' at index {idx} "
                f"missing keys: {sorted(missing_entry_keys)}"
            )
        extra_entry_keys = set(item.keys()) - required_entry_keys
        if extra_entry_keys:
            raise PCGEDataError(
                f"entries.json for version '{version}' at index {idx} "
                f"has unexpected keys: {sorted(extra_entry_keys)}"
            )

        code_val = item["code"]
        name_val = item["name"]
        parent_val = item["parent_code"]

        if not isinstance(code_val, str):
            raise PCGEDataError(
                f"entries.json for version '{version}' at index {idx} "
                "field 'code' must be a str"
            )
        if not isinstance(name_val, str):
            raise PCGEDataError(
                f"entries.json for version '{version}' at index {idx} "
                f"(code '{code_val}') field 'name' must be a str"
            )
        if parent_val is not None and not isinstance(parent_val, str):
            raise PCGEDataError(
                f"entries.json for version '{version}' at index {idx} "
                f"(code '{code_val}') field 'parent_code' must be str or None"
            )

        try:
            entry = PCGEEntry(code=code_val, name=name_val, parent_code=parent_val)
        except (TypeError, ValueError) as err:
            raise PCGEDataError(
                f"Invalid entry in entries.json for version '{version}' "
                f"at index {idx} (code '{code_val}'): {err}"
            ) from err
        entries_list.append(entry)

    try:
        return PCGECatalog(entries_list, metadata=metadata)
    except (TypeError, ValueError) as err:
        raise PCGEDataError(f"Catalog integrity validation failed: {err}") from err
