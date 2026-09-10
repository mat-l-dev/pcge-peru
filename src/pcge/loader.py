import hashlib
import importlib.resources as importlib_resources
import json
import re
from datetime import date
from typing import Any

from pcge.anomalies import PCGEAnomaly, PCGEAnomalyOccurrence
from pcge.catalog import PCGECatalog
from pcge.exceptions import PCGEDataError
from pcge.metadata import PCGEMetadata
from pcge.models import PCGEEntry
from pcge.provenance import PCGEProvenance


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


_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
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
    source_path = version_dir.joinpath("source.json")
    anomalies_path = version_dir.joinpath("anomalies.json")

    # 4. Leer metadata.json
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

    # 5. Leer entries.json como bytes
    try:
        entries_bytes = entries_path.read_bytes()
    except FileNotFoundError as err:
        raise PCGEDataError(
            f"Version '{version}' is not available: 'entries.json' not found"
        ) from err
    except OSError as err:
        raise PCGEDataError(
            f"Failed to read 'entries.json' for version '{version}': {err}"
        ) from err

    actual_dataset_sha256 = hashlib.sha256(entries_bytes).hexdigest().upper()

    try:
        entries_text = entries_bytes.decode("utf-8")
    except UnicodeDecodeError as err:
        raise PCGEDataError(
            f"Failed to decode 'entries.json' as UTF-8 for version '{version}': {err}"
        ) from err

    # 6. Leer source.json
    try:
        source_text = source_path.read_text(encoding="utf-8")
    except FileNotFoundError as err:
        raise PCGEDataError(
            f"Version '{version}' is not available: 'source.json' not found"
        ) from err
    except OSError as err:
        raise PCGEDataError(
            f"Failed to read 'source.json' for version '{version}': {err}"
        ) from err
    except UnicodeDecodeError as err:
        raise PCGEDataError(
            f"Failed to decode 'source.json' as UTF-8 for version '{version}': {err}"
        ) from err

    # 7. Leer anomalies.json
    try:
        anomalies_text = anomalies_path.read_text(encoding="utf-8")
    except FileNotFoundError as err:
        raise PCGEDataError(
            f"Version '{version}' is not available: 'anomalies.json' not found"
        ) from err
    except OSError as err:
        raise PCGEDataError(
            f"Failed to read 'anomalies.json' for version '{version}': {err}"
        ) from err
    except UnicodeDecodeError as err:
        raise PCGEDataError(
            f"Failed to decode 'anomalies.json' as UTF-8 for version '{version}': {err}"
        ) from err

    # 8. Parsear estrictamente metadata.json
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

    # 9-10. Parsear estrictamente source.json y construir PCGEProvenance
    raw_source = _loads_json_strict(source_text, "source.json", version)
    if not isinstance(raw_source, dict):
        raise PCGEDataError(
            f"source.json for version '{version}' must contain a JSON object"
        )

    required_source_keys = {
        "title",
        "authority",
        "resolution",
        "resolution_date",
        "publication_date",
        "mandatory_effective_date",
        "resolution_url",
        "source_filename",
        "source_sha256",
        "dataset_sha256",
        "catalog_chapter",
        "catalog_pdf_pages",
        "catalog_printed_pages",
    }
    missing_source = required_source_keys - set(raw_source.keys())
    if missing_source:
        raise PCGEDataError(
            f"source.json for version '{version}' missing required keys: "
            f"{sorted(missing_source)}"
        )
    extra_source = set(raw_source.keys()) - required_source_keys
    if extra_source:
        raise PCGEDataError(
            f"source.json for version '{version}' has unexpected extra keys: "
            f"{sorted(extra_source)}"
        )

    parsed_dates: dict[str, date] = {}
    for date_field in (
        "resolution_date",
        "publication_date",
        "mandatory_effective_date",
    ):
        date_str = raw_source[date_field]
        if not isinstance(date_str, str):
            raise PCGEDataError(
                f"source.json for version '{version}': '{date_field}' must be a "
                f"str, got {type(date_str).__name__}"
            )
        if not _DATE_RE.match(date_str):
            raise PCGEDataError(
                f"source.json for version '{version}': invalid date format "
                f"for '{date_field}': expected YYYY-MM-DD, got {date_str!r}"
            )
        try:
            parsed_dates[date_field] = date.fromisoformat(date_str)
        except ValueError as err:
            raise PCGEDataError(
                f"source.json for version '{version}': invalid date format "
                f"for '{date_field}': {err}"
            ) from err

    parsed_ranges: dict[str, tuple[int, int]] = {}
    for range_field in ("catalog_pdf_pages", "catalog_printed_pages"):
        range_obj = raw_source[range_field]
        if not isinstance(range_obj, dict):
            raise PCGEDataError(
                f"source.json for version '{version}': '{range_field}' must be an "
                f"object, got {type(range_obj).__name__}"
            )
        required_range_keys = {"first", "last"}
        missing_rk = required_range_keys - set(range_obj.keys())
        if missing_rk:
            raise PCGEDataError(
                f"source.json for version '{version}': '{range_field}' missing "
                f"required keys: {sorted(missing_rk)}"
            )
        extra_rk = set(range_obj.keys()) - required_range_keys
        if extra_rk:
            raise PCGEDataError(
                f"source.json for version '{version}': '{range_field}' has "
                f"unexpected extra keys: {sorted(extra_rk)}"
            )
        first_val = range_obj["first"]
        last_val = range_obj["last"]
        if isinstance(first_val, bool) or not isinstance(first_val, int):
            raise PCGEDataError(
                f"source.json for version '{version}': '{range_field}.first' must "
                f"be an int, got {type(first_val).__name__}"
            )
        if isinstance(last_val, bool) or not isinstance(last_val, int):
            raise PCGEDataError(
                f"source.json for version '{version}': '{range_field}.last' must "
                f"be an int, got {type(last_val).__name__}"
            )
        parsed_ranges[range_field] = (first_val, last_val)

    try:
        provenance = PCGEProvenance(
            title=raw_source["title"],
            authority=raw_source["authority"],
            resolution=raw_source["resolution"],
            resolution_date=parsed_dates["resolution_date"],
            publication_date=parsed_dates["publication_date"],
            mandatory_effective_date=parsed_dates["mandatory_effective_date"],
            resolution_url=raw_source["resolution_url"],
            source_filename=raw_source["source_filename"],
            source_sha256=raw_source["source_sha256"],
            catalog_chapter=raw_source["catalog_chapter"],
            catalog_pdf_pages=parsed_ranges["catalog_pdf_pages"],
            catalog_printed_pages=parsed_ranges["catalog_printed_pages"],
            dataset_sha256=raw_source["dataset_sha256"],
        )
    except (TypeError, ValueError) as err:
        raise PCGEDataError(
            f"Invalid provenance in 'source.json' for version '{version}': {err}"
        ) from err

    # 11. Calcular/verificar dataset_sha256
    if actual_dataset_sha256 != provenance.dataset_sha256:
        raise PCGEDataError(
            f"Integrity check failed for version '{version}': 'entries.json' "
            f"SHA-256 hash mismatch (expected {provenance.dataset_sha256}, "
            f"got {actual_dataset_sha256})"
        )

    # 12-13. Parsear estrictamente entries.json y construir PCGEEntry
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

    # 14-15. Parsear estrictamente anomalies.json y construir PCGEAnomaly
    raw_anomalies = _loads_json_strict(anomalies_text, "anomalies.json", version)
    if not isinstance(raw_anomalies, list):
        raise PCGEDataError(
            f"anomalies.json for version '{version}' must contain a JSON array"
        )

    base_required_keys = {
        "id",
        "type",
        "status",
        "description",
        "decision",
        "confirmation_no_invented_code",
        "occurrences",
    }
    anomalies_list: list[PCGEAnomaly] = []

    for a_idx, a_item in enumerate(raw_anomalies):
        if not isinstance(a_item, dict):
            raise PCGEDataError(
                f"anomalies.json for version '{version}' at index {a_idx} "
                "must be a JSON object"
            )
        keys = set(a_item.keys())
        missing_base = base_required_keys - keys
        if missing_base:
            raise PCGEDataError(
                f"anomalies.json for version '{version}' at index {a_idx} "
                f"missing required keys: {sorted(missing_base)}"
            )

        has_code = "code" in keys
        has_codes = "codes" in keys
        if has_code and has_codes:
            raise PCGEDataError(
                f"anomalies.json for version '{version}' at index {a_idx} "
                "cannot contain both 'code' and 'codes'"
            )
        if not has_code and not has_codes:
            raise PCGEDataError(
                f"anomalies.json for version '{version}' at index {a_idx} "
                "must contain either 'code' or 'codes'"
            )

        allowed_keys = base_required_keys | ({"code"} if has_code else {"codes"})
        extra_anomaly_keys = keys - allowed_keys
        if extra_anomaly_keys:
            raise PCGEDataError(
                f"anomalies.json for version '{version}' at index {a_idx} "
                f"has unexpected extra keys: {sorted(extra_anomaly_keys)}"
            )

        if has_code:
            code_val = a_item["code"]
            if not isinstance(code_val, str):
                raise PCGEDataError(
                    f"anomalies.json for version '{version}' at index {a_idx}: "
                    f"'code' must be a str, got {type(code_val).__name__}"
                )
            codes_tuple = (code_val,)
        else:
            codes_val = a_item["codes"]
            if not isinstance(codes_val, list):
                raise PCGEDataError(
                    f"anomalies.json for version '{version}' at index {a_idx}: "
                    f"'codes' must be a list, got {type(codes_val).__name__}"
                )
            for c_idx, c in enumerate(codes_val):
                if not isinstance(c, str):
                    raise PCGEDataError(
                        f"anomalies.json for version '{version}' at index {a_idx}: "
                        f"'codes[{c_idx}]' must be a str, got {type(c).__name__}"
                    )
            codes_tuple = tuple(codes_val)

        raw_occurrences = a_item["occurrences"]
        if not isinstance(raw_occurrences, list):
            raise PCGEDataError(
                f"anomalies.json for version '{version}' at index {a_idx}: "
                f"'occurrences' must be a list, got {type(raw_occurrences).__name__}"
            )

        required_occ_keys = {
            "occurrence_index",
            "pdf_page",
            "printed_page",
            "printed_code",
            "printed_name",
            "printed_parent_code",
            "disposition",
        }
        occurrences_list: list[PCGEAnomalyOccurrence] = []
        for occ_idx, occ_item in enumerate(raw_occurrences):
            if not isinstance(occ_item, dict):
                raise PCGEDataError(
                    f"anomalies.json for version '{version}' at anomaly index {a_idx}, "
                    f"occurrence index {occ_idx} must be a JSON object"
                )
            occ_keys = set(occ_item.keys())
            missing_occ = required_occ_keys - occ_keys
            if missing_occ:
                raise PCGEDataError(
                    f"anomalies.json for version '{version}' at anomaly index {a_idx}, "
                    f"occurrence index {occ_idx} missing required keys: "
                    f"{sorted(missing_occ)}"
                )
            extra_occ = occ_keys - required_occ_keys
            if extra_occ:
                raise PCGEDataError(
                    f"anomalies.json for version '{version}' at anomaly index {a_idx}, "
                    f"occurrence index {occ_idx} has unexpected extra keys: "
                    f"{sorted(extra_occ)}"
                )

            try:
                occurrence = PCGEAnomalyOccurrence(
                    occurrence_index=occ_item["occurrence_index"],
                    pdf_page=occ_item["pdf_page"],
                    printed_page=occ_item["printed_page"],
                    printed_code=occ_item["printed_code"],
                    printed_name=occ_item["printed_name"],
                    printed_parent_code=occ_item["printed_parent_code"],
                    disposition=occ_item["disposition"],
                )
            except (TypeError, ValueError) as err:
                raise PCGEDataError(
                    f"Invalid occurrence in 'anomalies.json' for version '{version}' "
                    f"at anomaly index {a_idx}, occurrence index {occ_idx}: {err}"
                ) from err
            occurrences_list.append(occurrence)

        try:
            anomaly = PCGEAnomaly(
                id=a_item["id"],
                type=a_item["type"],
                codes=codes_tuple,
                status=a_item["status"],
                description=a_item["description"],
                decision=a_item["decision"],
                confirmation_no_invented_code=a_item["confirmation_no_invented_code"],
                occurrences=tuple(occurrences_list),
            )
        except (TypeError, ValueError) as err:
            raise PCGEDataError(
                f"Invalid anomaly in 'anomalies.json' for version '{version}' "
                f"at index {a_idx}: {err}"
            ) from err
        anomalies_list.append(anomaly)

    # 16. Construir PCGECatalog
    try:
        return PCGECatalog(
            entries_list,
            metadata=metadata,
            provenance=provenance,
            anomalies=anomalies_list,
        )
    except (TypeError, ValueError) as err:
        raise PCGEDataError(f"Catalog integrity validation failed: {err}") from err
