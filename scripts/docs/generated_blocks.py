"""Shared helpers for generated Markdown blocks between HTML comment markers.

A block looks like::

    <!-- <name>:start (generiert: <command>) -->
    ... generated content ...
    <!-- <name>:end -->

The generators only replace the content between the markers; everything else
in the document stays hand-written.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class MarkerError(ValueError):
    """The document lacks the start/end markers of a generated block."""


def start_marker(name: str, command: str) -> str:
    return f"<!-- {name}:start (generiert: {command}) -->"


def end_marker(name: str) -> str:
    return f"<!-- {name}:end -->"


def _pattern(name: str) -> re.Pattern[str]:
    return re.compile(
        rf"(<!-- {re.escape(name)}:start[^>]*-->\n)(.*?)(<!-- {re.escape(name)}:end -->)",
        re.S,
    )


def has_block(text: str, name: str) -> bool:
    return _pattern(name).search(text) is not None


def replace_block(text: str, name: str, command: str, content: str) -> str:
    """Return ``text`` with the generated block ``name`` set to ``content``."""
    match = _pattern(name).search(text)
    if match is None:
        raise MarkerError(f"Markierungen <!-- {name}:start --> / <!-- {name}:end --> fehlen")
    body = content.rstrip("\n") + "\n"
    return (
        text[: match.start()]
        + start_marker(name, command)
        + "\n"
        + body
        + end_marker(name)
        + text[match.end() :]
    )


def sync_file(path: Path, name: str, command: str, content: str, *, write: bool) -> bool:
    """Update (``write``) or compare the block; return True when it was current."""
    text = path.read_text(encoding="utf-8")
    updated = replace_block(text, name, command, content)
    if updated == text:
        return True
    if write:
        path.write_text(updated, encoding="utf-8")
    return False


def md_cell(value: str) -> str:
    """Escape a value for a Markdown table cell."""
    return value.replace("|", "\\|").replace("\n", " ").strip() or "–"
