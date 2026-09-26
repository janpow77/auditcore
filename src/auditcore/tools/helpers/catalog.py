"""Catalog of auditcore library functions for classifying application helpers.

Two sources: the curated topic catalog (``data/catalog.json``, name patterns
with library targets) and, when the auditcore monorepo is available, an index
of normalised function hashes of all Python packages and ``@auditcore/*`` JS
packages. A hash hit means the application carries a verbatim copy.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from auditcore.tools.helpers.model import (
    PYTHON,
    FunctionInfo,
    SourceFile,
    as_dict,
    as_list,
    as_str,
    read_json,
    str_list,
)
from auditcore.tools.helpers.pyscan import scan_python
from auditcore.tools.helpers.sources import is_skipped
from auditcore.tools.helpers.tsscan import scan_typescript

CATALOG_PATH = Path(__file__).with_name("data") / "catalog.json"
AVAILABLE = "vorhanden"
MIN_TOKENS = 30


@dataclass(frozen=True)
class Target:
    """A library function that covers a topic."""

    library: str
    symbol: str
    status: str


@dataclass(frozen=True)
class Topic:
    """A helper topic recognised by the normalised function name."""

    id: str
    title: str
    languages: tuple[str, ...]
    pattern: re.Pattern[str]
    targets: tuple[Target, ...]
    contract: str = ""

    @property
    def available(self) -> Target | None:
        """The first target that already exists in a library."""
        return next((target for target in self.targets if target.status == AVAILABLE), None)


def normalised_name(name: str) -> str:
    """Last name segment without underscores, lower case."""
    return name.rsplit(".", 1)[-1].replace("_", "").lower()


def _topic(entry: dict[str, object]) -> Topic:
    targets = tuple(
        Target(as_str(item.get("library")), as_str(item.get("symbol")), as_str(item.get("status")))
        for item in map(as_dict, as_list(entry.get("targets")))
    )
    return Topic(
        id=as_str(entry.get("id")),
        title=as_str(entry.get("title")),
        languages=tuple(str_list(entry.get("languages"))),
        pattern=re.compile(as_str(entry.get("name"))),
        targets=targets,
        contract=as_str(entry.get("contract")),
    )


def load_topics(path: Path = CATALOG_PATH) -> list[Topic]:
    """Load the curated topic catalog."""
    data = as_dict(read_json(path))
    return [_topic(as_dict(entry)) for entry in as_list(data.get("topics"))]


def topic_of(function: FunctionInfo, topics: list[Topic]) -> Topic | None:
    """Return the first topic whose name pattern matches the function."""
    name = normalised_name(function.name)
    for topic in topics:
        if function.language in topic.languages and topic.pattern.search(name):
            return topic
    return None


@dataclass(frozen=True)
class LibraryFunction:
    """A function of an auditcore library, identified by its normalised body."""

    library: str
    symbol: str
    path: str


def _python_library_files(root: Path) -> list[tuple[str, SourceFile]]:
    found = []
    for path in sorted((root / "packages").glob("auditcore_*/src/**/*.py")):
        relative = path.relative_to(root).as_posix()
        if not is_skipped(relative):
            package = path.relative_to(root).parts[1]
            found.append((package, SourceFile(relative, PYTHON, path.read_text(encoding="utf-8"))))
    return found


def _js_packages(root: Path) -> dict[str, str]:
    packages = {}
    for manifest in sorted((root / "packages-js").glob("*/package.json")):
        name = as_str(as_dict(read_json(manifest)).get("name"), manifest.parent.name)
        packages[manifest.parent.relative_to(root).as_posix()] = name
    return packages


def _js_library_files(root: Path) -> list[str]:
    files = []
    for suffix in ("ts", "tsx", "vue", "js"):
        for path in (root / "packages-js").glob(f"*/src/**/*.{suffix}"):
            relative = path.relative_to(root).as_posix()
            if not is_skipped(relative):
                files.append(relative)
    return sorted(files)


def library_index(root: Path, *, with_js: bool = True) -> dict[str, list[LibraryFunction]]:
    """Index normalised body hashes of all library functions of the monorepo at ``root``."""
    index: dict[str, list[LibraryFunction]] = {}

    def add(library: str, function: FunctionInfo) -> None:
        """Record one library function with enough substance."""
        if function.tokens >= MIN_TOKENS:
            entry = LibraryFunction(library, function.name, f"{function.path}:{function.line}")
            index.setdefault(function.body_hash, []).append(entry)

    for package, file in _python_library_files(root):
        for function in scan_python(file):
            add(package, function)
    if with_js and (root / "packages-js").is_dir():
        packages = _js_packages(root)
        functions, _errors = scan_typescript(root, _js_library_files(root))
        for function in functions:
            prefix = "/".join(function.path.split("/")[:2])
            add(packages.get(prefix, prefix), function)
    return index
