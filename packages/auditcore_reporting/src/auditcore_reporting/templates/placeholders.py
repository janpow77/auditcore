"""Inline placeholders ``{{ pfad }}``, ``{{ pfad | filter }}`` and ``{{ textbaustein.ID }}``.

The syntax is a strict subset of Jinja/docxtpl expressions: no function calls,
no arithmetic, no attribute access beyond dotted data paths. Everything else
is rejected when the template is defined, not silently left in the output.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass

from .errors import TemplateError
from .values import FILTERS, checked_text, format_value, lookup, valid_path

PLACEHOLDER = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)
BLOCK_ROOT = "textbaustein"
_ID = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*")


@dataclass(frozen=True)
class Placeholder:
    """Parsed placeholder: a data path with optional filter or a text block id."""

    path: str
    filter: str | None = None
    block: str | None = None


def parse_placeholder(expression: str, where: str) -> Placeholder:
    """Parse the text between ``{{`` and ``}}``."""
    parts = [part.strip() for part in expression.split("|")]
    if len(parts) > 2 or not parts[0]:
        raise TemplateError(f"{where}: ungültiger Platzhalter {{{{{expression}}}}}.")
    path = parts[0]
    if path.startswith(BLOCK_ROOT + "."):
        block = path[len(BLOCK_ROOT) + 1 :]
        if len(parts) > 1 or not _ID.fullmatch(block):
            raise TemplateError(f"{where}: ungültiger Textbaustein-Platzhalter {path!r}.")
        return Placeholder(path, block=block)
    if not valid_path(path):
        raise TemplateError(f"{where}: ungültiger Datenpfad {path!r} im Platzhalter.")
    filter_name = parts[1] if len(parts) > 1 else None
    if filter_name is not None and filter_name not in FILTERS:
        raise TemplateError(
            f"{where}: unbekannter Filter {filter_name!r}; erlaubt: {', '.join(FILTERS)}."
        )
    return Placeholder(path, filter_name)


def placeholders(text: str, where: str) -> Iterator[Placeholder]:
    """All placeholders of ``text``; a lone ``{{`` or ``}}`` is an error."""
    checked_text(text, where)
    for match in PLACEHOLDER.finditer(text):
        yield parse_placeholder(match.group(1), where)
    rest = PLACEHOLDER.sub("", text)
    if "{{" in rest or "}}" in rest:
        raise TemplateError(f"{where}: nicht geschlossener Platzhalter.")
    if "{%" in rest or "%}" in rest:
        raise TemplateError(f"{where}: Steuer-Tags {{% … %}} gibt es nur in DOCX-Vorlagen.")


@dataclass(frozen=True)
class Scope:
    """Data visible to placeholders plus the resolver for text blocks."""

    values: Mapping[str, object]
    block_text: Callable[[str, Scope], str]

    def bind(self, name: str, value: object) -> Scope:
        """New scope with a loop variable."""
        return Scope({**self.values, name: value}, self.block_text)


def substitute(text: str, scope: Scope, where: str) -> str:
    """Replace every placeholder in ``text``."""

    def replace(match: re.Match[str]) -> str:
        placeholder = parse_placeholder(match.group(1), where)
        if placeholder.block is not None:
            return scope.block_text(placeholder.block, scope)
        value = lookup(scope.values, placeholder.path)
        return format_value(value, placeholder.filter, f"{where}: {placeholder.path}")

    return PLACEHOLDER.sub(replace, text)
