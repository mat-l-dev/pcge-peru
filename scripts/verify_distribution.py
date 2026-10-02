import argparse
import email
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = REPO_ROOT / "dist"
SMOKE_SCRIPT = REPO_ROOT / "scripts" / "smoke_catalog.py"


def verify_wheel(wheel_path: Path) -> None:
    print(f"Verifying wheel: {wheel_path.name}")
    with zipfile.ZipFile(wheel_path) as zf:
        names = set(zf.namelist())

        required_entries = [
            "pcge/py.typed",
            "pcge/data/2019/entries.json",
            "pcge/data/2019/metadata.json",
            "pcge/data/2019/source.json",
            "pcge/data/2019/anomalies.json",
            "pcge/data/2026/entries.json",
            "pcge/data/2026/metadata.json",
            "pcge/data/2026/source.json",
            "pcge/data/2026/anomalies.json",
        ]
        for entry in required_entries:
            assert entry in names, f"Wheel missing required file: {entry}"

        for name in names:
            assert "validation.py" not in name, (
                f"Wheel must not contain validation.py, found: {name}"
            )

        metadata_entries = [n for n in names if n.endswith(".dist-info/METADATA")]
        assert len(metadata_entries) == 1, (
            f"Expected exactly 1 METADATA file in wheel, found: {metadata_entries}"
        )

        metadata_bytes = zf.read(metadata_entries[0])
        msg = email.message_from_bytes(metadata_bytes)

        with (REPO_ROOT / "pyproject.toml").open("rb") as project_file:
            project = tomllib.load(project_file)["project"]
        for field, expected in (
            ("Name", project["name"]),
            ("Version", project["version"]),
            ("Requires-Python", project["requires-python"]),
        ):
            actual = msg.get(field)
            if field == "Requires-Python" and actual is not None:
                actual = set(actual.split(","))
                expected = set(expected.split(","))
            assert actual == expected, (
                f"Expected {field}: {expected!r}, got: {actual!r}"
            )

        license_files = msg.get_all("License-File") or []
        assert license_files == project["license-files"], (
            f"Expected license files {project['license-files']}, got {license_files}"
        )
        dist_info = metadata_entries[0].rsplit("/", 1)[0]
        for license_file in license_files:
            assert f"{dist_info}/licenses/{license_file}" in names, (
                f"Wheel missing license file: {license_file}"
            )

        license_expr = msg.get("License-Expression")
        assert license_expr == "Apache-2.0", (
            f"Expected License-Expression: Apache-2.0, got: {license_expr!r}"
        )

        requires_dist = msg.get_all("Requires-Dist") or []
        assert not requires_dist, (
            f"Expected zero Requires-Dist in wheel, got: {requires_dist}"
        )
    print("  -> Wheel verification passed.")


def verify_sdist(sdist_path: Path) -> None:
    print(f"Verifying sdist: {sdist_path.name}")
    with tarfile.open(sdist_path, "r:gz") as tf:
        sdist_names = set(tf.getnames())

        def has_file(relative_path: str) -> bool:
            return any(name.split("/", 1)[-1] == relative_path for name in sdist_names)

        required_files = [
            "LICENSE",
            "README.md",
            "pyproject.toml",
            "schemas/entries.schema.json",
            "schemas/metadata.schema.json",
            "schemas/source.schema.json",
            "schemas/anomalies.schema.json",
            "src/pcge/py.typed",
            "src/pcge/data/2019/entries.json",
            "src/pcge/data/2019/metadata.json",
            "src/pcge/data/2019/source.json",
            "src/pcge/data/2019/anomalies.json",
            "src/pcge/data/2026/entries.json",
            "src/pcge/data/2026/metadata.json",
            "src/pcge/data/2026/source.json",
            "src/pcge/data/2026/anomalies.json",
        ]
        for req in required_files:
            assert has_file(req), f"Sdist missing required file: {req}"
    print("  -> Sdist verification passed.")


def verify_installed_wheel(wheel_path: Path) -> None:
    """Test the exact wheel in a fresh venv outside the checkout."""
    print(f"Testing isolated installation: {wheel_path.name}")
    with tempfile.TemporaryDirectory() as td:
        temp_dir = Path(td)
        venv_dir = temp_dir / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
        if sys.platform == "win32":
            venv_python = venv_dir / "Scripts" / "python.exe"
        else:
            venv_python = venv_dir / "bin" / "python"

        subprocess.run(
            [
                str(venv_python),
                "-I",
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-index",
                "--no-deps",
                str(wheel_path.resolve()),
            ],
            check=True,
        )
        smoke_script = temp_dir / "smoke_catalog.py"
        shutil.copyfile(SMOKE_SCRIPT, smoke_script)
        subprocess.run(
            [str(venv_python), "-I", str(smoke_script)],
            cwd=str(temp_dir),
            check=True,
        )
    print("  -> Isolated wheel installation passed.")


def verify_build_from_sdist(sdist_path: Path) -> None:
    print(f"Testing build from sdist: {sdist_path.name}")
    with tempfile.TemporaryDirectory() as td:
        temp_dir = Path(td)
        with tarfile.open(sdist_path, "r:gz") as tf:
            tf.extractall(temp_dir, filter="data")

        extracted_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
        assert len(extracted_dirs) == 1, (
            f"Expected 1 directory in unpacked sdist, found {extracted_dirs}"
        )
        source_tree = extracted_dirs[0]
        wheel_out = temp_dir / "wheel_out"
        wheel_out.mkdir()
        subprocess.run(
            [
                sys.executable,
                "-m",
                "build",
                "--wheel",
                "--outdir",
                str(wheel_out),
            ],
            cwd=str(source_tree),
            check=True,
        )
        built_wheels = list(wheel_out.glob("*.whl"))
        assert len(built_wheels) == 1, f"Expected 1 built wheel, found {built_wheels}"
        verify_wheel(built_wheels[0])
        verify_installed_wheel(built_wheels[0])
    print("  -> Build and test from sdist passed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify built distribution artifacts.")
    parser.add_argument(
        "--skip-sdist-rebuild",
        action="store_true",
        help="Verify and install downloaded artifacts without rebuilding the sdist.",
    )
    args = parser.parse_args()

    if not DIST_DIR.is_dir():
        print(f"Dist directory not found at {DIST_DIR}", file=sys.stderr)
        sys.exit(1)

    wheels = list(DIST_DIR.glob("*.whl"))
    sdists = list(DIST_DIR.glob("*.tar.gz"))
    if len(wheels) != 1:
        print(
            f"Expected exactly 1 wheel in {DIST_DIR}, found {len(wheels)}",
            file=sys.stderr,
        )
        sys.exit(1)
    if len(sdists) != 1:
        print(
            f"Expected exactly 1 sdist in {DIST_DIR}, found {len(sdists)}",
            file=sys.stderr,
        )
        sys.exit(1)

    verify_wheel(wheels[0])
    verify_sdist(sdists[0])
    verify_installed_wheel(wheels[0])
    if not args.skip_sdist_rebuild:
        verify_build_from_sdist(sdists[0])
    print("\nAll distribution artifact checks passed successfully.")


if __name__ == "__main__":
    main()
