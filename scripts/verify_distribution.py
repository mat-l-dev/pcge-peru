import email
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = REPO_ROOT / "dist"


def verify_wheel(wheel_path: Path) -> None:
    print(f"Verifying wheel: {wheel_path.name}")
    with zipfile.ZipFile(wheel_path) as zf:
        names = set(zf.namelist())

        required_entries = [
            "pcge/py.typed",
            "pcge/data/2019/entries.json",
            "pcge/data/2019/metadata.json",
            "pcge/data/2026/entries.json",
            "pcge/data/2026/metadata.json",
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
            "sources/2019/source.json",
            "sources/2019/anomalies.json",
            "sources/2026/source.json",
            "sources/2026/anomalies.json",
            "src/pcge/py.typed",
            "src/pcge/data/2019/entries.json",
            "src/pcge/data/2019/metadata.json",
            "src/pcge/data/2026/entries.json",
            "src/pcge/data/2026/metadata.json",
        ]
        for req in required_files:
            assert has_file(req), f"Sdist missing required file: {req}"
    print("  -> Sdist verification passed.")


def verify_build_from_sdist(sdist_path: Path) -> None:
    print(f"Testing build from sdist: {sdist_path.name}")
    with tempfile.TemporaryDirectory() as td:
        temp_dir = Path(td)
        with tarfile.open(sdist_path, "r:gz") as tf:
            tf.extractall(temp_dir)

        extracted_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
        assert len(extracted_dirs) == 1, (
            f"Expected 1 directory in unpacked sdist, found {extracted_dirs}"
        )
        source_tree = extracted_dirs[0]

        wheel_out = temp_dir / "wheel_out"
        wheel_out.mkdir()

        cmd_build = [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--outdir",
            str(wheel_out),
        ]
        subprocess.run(cmd_build, cwd=str(source_tree), check=True)

        built_wheels = list(wheel_out.glob("*.whl"))
        assert len(built_wheels) == 1, f"Expected 1 built wheel, found {built_wheels}"
        new_wheel = built_wheels[0]

        # Verify wheel content from sdist
        verify_wheel(new_wheel)

        # Create isolated venv and install
        venv_dir = temp_dir / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
        if sys.platform == "win32":
            venv_python = venv_dir / "Scripts" / "python.exe"
        else:
            venv_python = venv_dir / "bin" / "python"

        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "--no-deps", str(new_wheel)],
            check=True,
        )

        smoke_script = temp_dir / "test_smoke.py"
        smoke_script.write_text(
            (
                "import importlib.resources as importlib_resources\n"
                "from pcge import load_catalog\n\n"
                'cat_2019 = load_catalog("2019")\n'
                'assert len(cat_2019) == 1757, f"Expected 1757, got {len(cat_2019)}"\n'
                "assert cat_2019.metadata is not None\n"
                'assert cat_2019.metadata.pcge_version == "2019"\n'
                'assert "10" in cat_2019\n'
                'assert cat_2019["10"].name == (\n'
                '    "EFECTIVO Y EQUIVALENTES DE EFECTIVO"\n'
                ")\n\n"
                'cat_2026 = load_catalog("2026")\n'
                'assert len(cat_2026) == 1636, f"Expected 1636, got {len(cat_2026)}"\n'
                "assert cat_2026.metadata is not None\n"
                'assert cat_2026.metadata.pcge_version == "2026"\n'
                'assert "10" in cat_2026\n'
                'assert cat_2026["10"].name == (\n'
                '    "EFECTIVO Y EQUIVALENTES AL EFECTIVO"\n'
                ")\n\n"
                'pkg_files = importlib_resources.files("pcge")\n'
                'assert pkg_files.joinpath("py.typed").is_file()\n'
                'print("Smoke test on sdist-built wheel passed successfully.")\n'
            ),
            encoding="utf-8",
        )

        subprocess.run(
            [str(venv_python), str(smoke_script)],
            cwd=str(temp_dir),
            check=True,
        )
    print("  -> Build and test from sdist passed.")


def main() -> None:
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
    verify_build_from_sdist(sdists[0])
    print("\nAll distribution artifact checks passed successfully.")


if __name__ == "__main__":
    main()
