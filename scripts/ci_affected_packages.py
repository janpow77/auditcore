"""Choose the domain packages a CI run has to verify.

On main and for manual runs every package is verified. On a pull request only
the changed packages and every package that depends on them (transitively)
are verified, together with the internal packages they require (transitively):
an exact pin such as ``auditcore_harvest==0.1.1`` can only be installed if that
version is built in the same run. A change to shared build tooling selects every package.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import tomllib
from pathlib import Path

SHARED_PREFIXES = (
    "packaging/",
    "src/auditcore/tools/deployer/",
    "src/auditcore/tools/quality/",
    "scripts/verify_domain_packages.py",
    "scripts/verify_optional_renderers.py",
    "scripts/prepare_library_release.py",
    "scripts/verify_code_quality.py",
    "scripts/ci_affected_packages.py",
    "requirements/ci.lock",
    ".github/workflows/domain-packages.yml",
)
REQUIREMENT_NAME = re.compile(r"^\s*([A-Za-z0-9_.-]+)")


def all_packages(root: Path) -> dict[str, Path]:
    packages: dict[str, Path] = {}
    for pyproject in sorted(root.glob("packages/*/pyproject.toml")):
        name = tomllib.loads(pyproject.read_text())["project"]["name"]
        packages[normalise(name)] = pyproject.parent
    return packages


def normalise(name: str) -> str:
    return re.sub(r"[-_.]+", "_", name).lower()


def internal_dependencies(directory: Path, known: set[str]) -> set[str]:
    project = tomllib.loads((directory / "pyproject.toml").read_text())["project"]
    requirements = list(project.get("dependencies", []))
    for extra in project.get("optional-dependencies", {}).values():
        requirements.extend(extra)
    names = set()
    for requirement in requirements:
        match = REQUIREMENT_NAME.match(requirement)
        if match and normalise(match.group(1)) in known:
            names.add(normalise(match.group(1)))
    return names


def changed_files(base: str) -> list[str]:
    output = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [line for line in output.splitlines() if line]


def select(root: Path, files: list[str]) -> list[Path]:
    packages = all_packages(root)
    if any(file.startswith(SHARED_PREFIXES) for file in files):
        return list(packages.values())
    by_directory = {path.name: name for name, path in packages.items()}
    selected = {
        by_directory[file.split("/")[1]]
        for file in files
        if file.startswith("packages/") and file.split("/")[1] in by_directory
    }
    dependents = {
        name: internal_dependencies(path, set(packages)) for name, path in packages.items()
    }
    grew = True
    while grew:
        additions = {name for name, deps in dependents.items() if deps & selected} - selected
        selected |= additions
        grew = bool(additions)
    grew = True
    while grew:
        additions = set().union(*(dependents[name] for name in selected)) - selected
        selected |= additions
        grew = bool(additions)
    return [packages[name] for name in sorted(selected)]


def select_tests(root: Path, files: list[str]) -> list[Path]:
    """Choose conventional module tests and fall back to package test directories."""
    selected: set[Path] = set()
    for package in select(root, files):
        prefix = f"{package.relative_to(root).as_posix()}/src/"
        changed = [Path(file) for file in files if file.startswith(prefix) and file.endswith(".py")]
        module_tests = {
            package / "tests" / f"test_{source.stem}.py"
            for source in changed
            if (package / "tests" / f"test_{source.stem}.py").is_file()
        }
        selected.update(
            module_tests or ({package / "tests"} if (package / "tests").is_dir() else set())
        )
    if any(file.startswith(("src/", "tests/")) for file in files):
        candidates = {
            root / "tests" / f"test_{Path(file).stem}.py"
            for file in files
            if file.startswith("src/") and file.endswith(".py")
        }
        existing = {path for path in candidates if path.is_file()}
        selected.update(existing or {root / "tests"})
    return sorted(selected)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="Base ref of a pull request; omit to select all")
    parser.add_argument("--tests", action="store_true", help="Testpfade statt Paketpfade ausgeben")
    args = parser.parse_args()
    root = Path.cwd()
    if args.base:
        files = changed_files(args.base)
        chosen = select_tests(root, files) if args.tests else select(root, files)
    else:
        chosen = (
            [root / "tests", *(path / "tests" for path in all_packages(root).values())]
            if args.tests
            else list(all_packages(root).values())
        )
        chosen = [path for path in chosen if path.is_dir()]
    # No trailing empty line: the workflow tests the file with ``-s`` and would
    # otherwise build the platform and call pip without any package.
    for path in chosen:
        print(path.relative_to(root))


if __name__ == "__main__":
    main()
