import importlib.resources as importlib_resources
import json

from pcge.catalog import PCGECatalog
from pcge.exceptions import PCGEDataError
from pcge.metadata import PCGEMetadata
from pcge.models import PCGEEntry
from pcge.validation import validate_dataset


def load_catalog(version: str = "2026") -> PCGECatalog:
    if not isinstance(version, str):
        item_type = type(version).__name__
        raise TypeError(f"version must be a str, got {item_type}")
    if not version:
        raise PCGEDataError("version cannot be empty")
    if not (version.isascii() and version.isdigit()):
        raise PCGEDataError(f"version must contain only ASCII digits, got {version!r}")

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

    try:
        raw_metadata = json.loads(metadata_text)
    except json.JSONDecodeError as err:
        raise PCGEDataError(
            f"Malformed JSON in 'metadata.json' for version '{version}': {err}"
        ) from err

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

    try:
        raw_entries = json.loads(entries_text)
    except json.JSONDecodeError as err:
        raise PCGEDataError(
            f"Malformed JSON in 'entries.json' for version '{version}': {err}"
        ) from err

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

    validated_entries = validate_dataset(entries_list, metadata)
    return PCGECatalog(validated_entries, metadata=metadata)
