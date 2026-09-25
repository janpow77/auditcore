"""``scan``: find helper functions, group duplicates, classify against the catalog."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from auditcore.tools.helpers.catalog import (
    MIN_TOKENS,
    LibraryFunction,
    Topic,
    library_index,
    load_topics,
    topic_of,
)
from auditcore.tools.helpers.model import PYTHON, TYPESCRIPT, FunctionInfo, SourceFile
from auditcore.tools.helpers.pyscan import scan_python
from auditcore.tools.helpers.sources import read_sources
from auditcore.tools.helpers.tsscan import scan_typescript

EXACT = "exakt"
BY_NAME = "name"


@dataclass
class Inventory:
    """Source files and functions of one repository."""

    root: Path
    files: list[SourceFile]
    functions: list[FunctionInfo]
    errors: list[str] = field(default_factory=list)


def collect(root: Path, excludes: list[str], *, with_ts: bool = True) -> Inventory:
    """Read the sources of ``root`` and extract all functions."""
    files = read_sources(root, excludes)
    functions: list[FunctionInfo] = []
    for file in files:
        if file.language == PYTHON:
            functions.extend(scan_python(file))
    errors: list[str] = []
    ts_files = [file.path for file in files if file.language == TYPESCRIPT]
    if ts_files and with_ts:
        found, errors = scan_typescript(root, ts_files)
        functions.extend(found)
    elif ts_files:
        errors.append(f"{len(ts_files)} TS/JS/Vue-Dateien ohne Node-Analyse (--no-node)")
    return Inventory(root, files, functions, errors)


@dataclass(frozen=True)
class LibraryMatch:
    """An application helper that an auditcore library covers (or will cover)."""

    function: FunctionInfo
    match: str
    topic: str
    title: str
    library: str
    symbol: str
    status: str
    contract: str = ""

    @property
    def key(self) -> str:
        """Ratchet key independent of line numbers."""
        return f"library|{self.function.path}|{self.function.name}|{self.library}"

    def to_dict(self) -> dict[str, object]:
        """Serialize for the JSON report."""
        return {
            **self.function.to_dict(),
            "match": self.match,
            "topic": self.topic,
            "title": self.title,
            "library": self.library,
            "symbol": self.symbol,
            "status": self.status,
            "contract": self.contract,
            "key": self.key,
        }


def _exact(function: FunctionInfo, hit: LibraryFunction) -> LibraryMatch:
    return LibraryMatch(
        function,
        EXACT,
        "wortgleich",
        "Wortgleiche Kopie",
        hit.library,
        f"{hit.symbol} ({hit.path})",
        "vorhanden",
    )


def _by_topic(function: FunctionInfo, topic: Topic) -> LibraryMatch:
    target = topic.available or topic.targets[0]
    return LibraryMatch(
        function,
        BY_NAME,
        topic.id,
        topic.title,
        target.library,
        target.symbol,
        target.status,
        topic.contract,
    )


def classify(
    functions: list[FunctionInfo],
    topics: list[Topic],
    index: dict[str, list[LibraryFunction]],
) -> list[LibraryMatch]:
    """Match every function against library hashes first, then against topics."""
    matches = []
    for function in functions:
        hits = index.get(function.body_hash, []) if function.tokens >= MIN_TOKENS else []
        if hits:
            matches.append(_exact(function, hits[0]))
            continue
        topic = topic_of(function, topics)
        if topic is not None and topic.targets:
            matches.append(_by_topic(function, topic))
    return matches


@dataclass(frozen=True)
class DuplicateGroup:
    """Functions with the same normalised body inside one repository."""

    body_hash: str
    tokens: int
    members: tuple[FunctionInfo, ...]

    def to_dict(self) -> dict[str, object]:
        """Serialize for the JSON report."""
        return {
            "body_hash": self.body_hash,
            "tokens": self.tokens,
            "count": len(self.members),
            "members": [f"{m.path}:{m.line} {m.name}" for m in self.members],
        }


def duplicate_groups(functions: list[FunctionInfo]) -> list[DuplicateGroup]:
    """Group functions with identical normalised bodies (at least ``MIN_TOKENS``)."""
    groups: dict[str, list[FunctionInfo]] = defaultdict(list)
    for function in functions:
        if function.tokens >= MIN_TOKENS:
            groups[f"{function.language}:{function.body_hash}"].append(function)
    result = [
        DuplicateGroup(key.split(":", 1)[1], members[0].tokens, tuple(members))
        for key, members in groups.items()
        if len(members) > 1
    ]
    return sorted(result, key=lambda group: (-len(group.members) * group.tokens, group.body_hash))


@dataclass
class ScanResult:
    """Everything ``scan`` found in one repository."""

    inventory: Inventory
    matches: list[LibraryMatch]
    duplicates: list[DuplicateGroup]
    library_root: Path | None

    @property
    def ratcheted(self) -> list[LibraryMatch]:
        """Matches that count against the baseline (library function exists)."""
        return [match for match in self.matches if match.status == "vorhanden"]


def run_scan(
    inventory: Inventory, library_root: Path | None, *, with_ts: bool = True
) -> ScanResult:
    """Classify the functions of an inventory."""
    index = library_index(library_root, with_js=with_ts) if library_root else {}
    matches = classify(inventory.functions, load_topics(), index)
    return ScanResult(inventory, matches, duplicate_groups(inventory.functions), library_root)
