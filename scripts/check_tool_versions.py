"""Check that CI and pre-commit use the same Ruff release."""

import re
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    versions = [
        match.group(1)
        for dependency in config["dependency-groups"]["dev"]
        if isinstance(dependency, str)
        and (match := re.fullmatch(r"ruff==([^\s]+)", dependency))
    ]
    hook_version = None
    ruff_repo = False
    for line in (
        (REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8").splitlines()
    ):
        if match := re.match(r"\s*- repo:\s*(\S+)", line):
            ruff_repo = match.group(1) == "https://github.com/astral-sh/ruff-pre-commit"
        elif ruff_repo and (match := re.match(r"\s*rev:\s*v([^\s#]+)", line)):
            hook_version = match.group(1)
            break

    if len(versions) != 1 or hook_version != versions[0]:
        sys.exit(
            "Ruff versions must match: "
            f"pyproject.toml={versions}, pre-commit={hook_version!r}. "
            "Update both pins together."
        )
    print(f"Ruff versions agree: {hook_version}")


if __name__ == "__main__":
    main()
