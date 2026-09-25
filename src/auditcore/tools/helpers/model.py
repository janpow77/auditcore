"""Shared data model and JSON helpers of ``auditcore-helpers``."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

#: Languages the tool distinguishes. ``ts`` covers TS, JS and Vue script blocks.
PYTHON = "python"
TYPESCRIPT = "ts"


MAX_MESSAGE = 160
#: Validation errors (pydantic settings) echo input values such as secrets from .env.
SECRET_ECHO = re.compile(r"(input_value|input)\s*=\s*('[^']*'|\"[^\"]*\"|\S+)")


def redact(text: str, *, last: bool = False) -> str:
    """One line of an error text, shortened and without echoed input values."""
    lines = [line for line in text.strip().splitlines() if line.strip()] or [""]
    line = SECRET_ECHO.sub(r"\1=***", lines[-1] if last else lines[0])
    return line if len(line) <= MAX_MESSAGE else line[: MAX_MESSAGE - 1] + "…"


class HelperToolError(RuntimeError):
    """The tool cannot run (missing Node toolchain, unreadable manifest, ...)."""


def as_dict(value: object) -> dict[str, object]:
    """Return ``value`` as a JSON object, or an empty dict."""
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    return {}


def as_list(value: object) -> list[object]:
    """Return ``value`` as a JSON array, or an empty list."""
    return list(value) if isinstance(value, list) else []


def as_str(value: object, default: str = "") -> str:
    """Return ``value`` if it is a string, else ``default``."""
    return value if isinstance(value, str) else default


def as_int(value: object, default: int = 0) -> int:
    """Return ``value`` if it is an integer (not bool), else ``default``."""
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def str_list(value: object) -> list[str]:
    """Return the string items of a JSON array."""
    return [item for item in as_list(value) if isinstance(item, str)]


def read_json(path: Path) -> object:
    """Read a UTF-8 JSON file."""
    loaded: object = json.loads(path.read_text(encoding="utf-8"))
    return loaded


def write_json(path: Path, data: object) -> None:
    """Write deterministic, human-readable JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def short_hash(text: str, length: int = 12) -> str:
    """Stable short SHA-1 digest used for fingerprints (not for security)."""
    return hashlib.sha1(text.encode("utf-8"), usedforsecurity=False).hexdigest()[:length]


@dataclass(frozen=True)
class FunctionInfo:
    """One helper function found by the scanner."""

    language: str
    path: str
    name: str
    kind: str
    line: int
    end_line: int
    tokens: int
    body_hash: str
    source: str
    exported: bool = False
    nested: bool = False
    params: int = 0
    prelude: tuple[str, ...] = ()

    @property
    def lines(self) -> int:
        """Length of the definition in lines."""
        return self.end_line - self.line + 1

    def to_dict(self) -> dict[str, object]:
        """Serialize without the (long) source text."""
        return {
            "language": self.language,
            "path": self.path,
            "name": self.name,
            "kind": self.kind,
            "line": self.line,
            "lines": self.lines,
            "tokens": self.tokens,
            "body_hash": self.body_hash,
            "exported": self.exported,
        }


@dataclass(frozen=True)
class Finding:
    """One lint finding; ``key`` identifies it independent of line numbers."""

    rule: str
    path: str
    line: int
    message: str
    snippet: str
    severity: str = "fehler"
    anchor: str = ""

    @property
    def key(self) -> str:
        """Ratchet key: rule, file and normalised snippet (or explicit anchor)."""
        anchor = self.anchor or " ".join(self.snippet.split())
        return f"lint|{self.rule}|{self.path}|{short_hash(anchor)}"

    def to_dict(self) -> dict[str, object]:
        """Serialize for the JSON report."""
        return {
            "rule": self.rule,
            "severity": self.severity,
            "path": self.path,
            "line": self.line,
            "message": self.message,
            "snippet": self.snippet,
            "key": self.key,
        }


@dataclass
class SourceFile:
    """A source file of the scanned repository."""

    path: str
    language: str
    text: str
    lines: list[str] = field(init=False)

    def __post_init__(self) -> None:
        self.lines = self.text.splitlines()

    def line_of(self, offset: int) -> int:
        """1-based line number of a character offset."""
        return self.text.count("\n", 0, offset) + 1

    def line_text(self, line: int) -> str:
        """Text of a 1-based line (empty when out of range)."""
        return self.lines[line - 1] if 0 < line <= len(self.lines) else ""
