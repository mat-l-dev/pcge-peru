import datetime
import importlib.resources as importlib_resources
import sys
from pathlib import Path

import pcge
from pcge import (
    PCGEAnomaly,
    PCGEAnomalyOccurrence,
    PCGEProvenance,
    available_versions,
    load_catalog,
)

assert Path(pcge.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
assert available_versions() == ("2019", "2026")

cat_2019 = load_catalog("2019")
assert len(cat_2019) == 1757, f"Expected 1757, got {len(cat_2019)}"
assert cat_2019.metadata is not None
assert cat_2019.metadata.pcge_version == "2019"
assert cat_2019.metadata.dataset_revision == 2
assert "10" in cat_2019
assert cat_2019["10"].name == ("EFECTIVO Y EQUIVALENTES DE EFECTIVO")
assert isinstance(cat_2019.provenance, PCGEProvenance)
assert (
    cat_2019.provenance.dataset_sha256 == "FC70E43B94D0718373AB3B9F81202731"
    "E5295EDEDF0DF75231A2FFB3C2BEEC04"
)
assert isinstance(cat_2019.provenance.resolution_date, datetime.date)
assert isinstance(cat_2019.anomalies, tuple)
assert len(cat_2019.anomalies) >= 1
assert isinstance(cat_2019.anomalies[0], PCGEAnomaly)
assert isinstance(cat_2019.anomalies[0].occurrences[0], PCGEAnomalyOccurrence)
assert len(cat_2019.anomalies_for("63432")) >= 1

cat_2026 = load_catalog("2026")
assert len(cat_2026) == 1636, f"Expected 1636, got {len(cat_2026)}"
assert cat_2026.metadata is not None
assert cat_2026.metadata.pcge_version == "2026"
assert cat_2026.metadata.dataset_revision == 2
assert "10" in cat_2026
assert cat_2026["10"].name == ("EFECTIVO Y EQUIVALENTES AL EFECTIVO")
assert isinstance(cat_2026.provenance, PCGEProvenance)
assert (
    cat_2026.provenance.dataset_sha256 == "DC8047E50C937312DA6F4BAB9E2D37A9"
    "A55DB478AA8B3605F7AB730FFDDBFA6A"
)
assert isinstance(cat_2026.provenance.publication_date, datetime.date)
assert isinstance(cat_2026.anomalies, tuple)
assert len(cat_2026.anomalies) >= 1
assert len(cat_2026.anomalies_for("70992")) >= 1

pkg_files = importlib_resources.files("pcge")
assert pkg_files.joinpath("py.typed").is_file()
print("Installed wheel smoke test passed successfully.")
