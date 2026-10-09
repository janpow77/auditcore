"""Parse the JSON block list of a structured template into :mod:`.model` blocks.

JSON form (``"if"`` is optional on every block)::

    {"type": "heading", "text": "1. Anlass", "level": 1}
    {"type": "paragraph", "text": "Az. {{ aktenzeichen }}"}
    {"type": "textblock", "id": "ohne_feststellungen"}
    {"type": "list", "source": "anlagen", "as": "a", "item": "{{ a.titel }}"}
    {"type": "table", "source": "positionen", "as": "p", "empty": "Keine Positionen.",
     "header_if_empty": true, "borders": "horizontal", "header_fill": "D9E2F3",
     "stripe": "F2F2F2", "row_fill": [{"if": {"greater": ["p.betrag", 1000]}, "bold": true}],
     "columns": [{"header": "Betrag", "cell": "{{ p.betrag | eur }}", "align": "right",
                  "width": 2, "fill": [{"if": "p.strittig", "color": "F8CBAD"}]}]}
    {"type": "fields", "empty": "—",
     "rows": [{"label": "Aktenzeichen", "value": "{{ aktenzeichen }}"}]}
    {"type": "pagebreak"}
    {"type": "heading", "text": "1. Anlass", "anchor": "anlass"}
    {"type": "paragraph", "text": "Siehe Anlass", "link": "anlass"}
    {"type": "image", "image": "wappen", "width_cm": 2.5, "align": "center", "alt": "Wappen"}
    {"type": "image", "source": "anlage.foto"}      # base64 or data: URI in the data
    {"type": "toc", "title": "Inhalt", "levels": 2}
    {"type": "section", "title": "Feststellung {{ f.nummer }}", "for": "feststellungen",
     "as": "f", "blocks": [...]}
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping

from .conditions import Condition
from .errors import TemplateError
from .model import (
    BORDERS,
    Block,
    BlockRef,
    BulletList,
    Column,
    Contents,
    Field,
    Fields,
    Fill,
    Heading,
    Image,
    PageBreak,
    Paragraph,
    Section,
    Table,
)

MAX_BLOCK_DEPTH = 8
_HEX = re.compile(r"[0-9A-F]{6}")
_ANCHOR = re.compile(r"[a-z][a-z0-9-]{0,31}")


def text_of(data: Mapping[str, object], key: str, where: str, default: str | None = None) -> str:
    """Required (or defaulted) text field."""
    value = data.get(key, default)
    if not isinstance(value, str):
        raise TemplateError(f"{where}.{key}: Text erwartet.")
    return value


def condition_of(data: Mapping[str, object], where: str) -> Condition | None:
    """Optional ``if`` condition (name or object)."""
    value = data.get("if")
    if value is None or isinstance(value, (str, Mapping)):
        return value
    raise TemplateError(f"{where}.if: Bedingung muss Name oder Objekt sein.")


def flag_of(data: Mapping[str, object], key: str, where: str) -> bool:
    """Optional ``true``/``false`` field (default ``false``)."""
    value = data.get(key, False)
    if not isinstance(value, bool):
        raise TemplateError(f"{where}.{key}: true oder false.")
    return value


def mapping_of(value: object, where: str) -> Mapping[str, object]:
    """JSON object with text keys."""
    if not isinstance(value, Mapping) or not all(isinstance(k, str) for k in value):
        raise TemplateError(f"{where}: Objekt erwartet.")
    return value


def list_of(value: object, where: str) -> list[object]:
    """JSON list."""
    if not isinstance(value, list):
        raise TemplateError(f"{where}: Liste erwartet.")
    return value


def anchor_of(data: Mapping[str, object], key: str, where: str) -> str:
    """Optional jump target ``[a-z][a-z0-9-]`` (≤ 32); ``auto-…`` is reserved."""
    value = text_of(data, key, where, "")
    if value and (not _ANCHOR.fullmatch(value) or value.startswith("auto-")):
        raise TemplateError(f"{where}.{key}: Sprungmarke aus a-z, 0-9, - (nicht 'auto-…').")
    return value


def _heading(data: Mapping[str, object], where: str, depth: int) -> Block:
    level = data.get("level", 1)
    if level not in (1, 2, 3):
        raise TemplateError(f"{where}.level: 1, 2 oder 3.")
    return Heading(
        text_of(data, "text", where), int(str(level)), condition_of(data, where),
        anchor_of(data, "anchor", where),
    )  # fmt: skip


def _paragraph(data: Mapping[str, object], where: str, depth: int) -> Block:
    return Paragraph(
        text_of(data, "text", where), condition_of(data, where), anchor_of(data, "link", where)
    )


def _number(data: Mapping[str, object], key: str, where: str, low: float, high: float) -> float:
    value = data.get(key, 0)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high:
        raise TemplateError(f"{where}.{key}: Zahl von {low:g} bis {high:g}.")
    return float(value)


def _image(data: Mapping[str, object], where: str, depth: int) -> Block:
    image, source = text_of(data, "image", where, ""), text_of(data, "source", where, "")
    if bool(image) == bool(source):
        raise TemplateError(f"{where}: genau eins von 'image' (Name) und 'source' (Datenpfad).")
    align = text_of(data, "align", where, "left")
    if align not in ("left", "right", "center"):
        raise TemplateError(f"{where}.align: left, right oder center.")
    return Image(
        image, source, _number(data, "width_cm", where, 0, 30), align,
        text_of(data, "alt", where, ""), condition_of(data, where),
    )  # fmt: skip


def _contents(data: Mapping[str, object], where: str, depth: int) -> Block:
    levels = data.get("levels", 2)
    if levels not in (1, 2, 3):
        raise TemplateError(f"{where}.levels: 1, 2 oder 3.")
    return Contents(
        text_of(data, "title", where, "Inhalt"), int(str(levels)), condition_of(data, where)
    )


def _textblock(data: Mapping[str, object], where: str, depth: int) -> Block:
    return BlockRef(text_of(data, "id", where), condition_of(data, where))


def _list(data: Mapping[str, object], where: str, depth: int) -> Block:
    return BulletList(
        text_of(data, "source", where),
        text_of(data, "item", where),
        text_of(data, "as", where, "eintrag"),
        condition_of(data, where),
        text_of(data, "empty", where, ""),
    )


def color_of(data: Mapping[str, object], key: str, where: str) -> str:
    """Optional colour ``RRGGBB`` (upper case) or ``""``."""
    value = text_of(data, key, where, "")
    if value and not _HEX.fullmatch(value):
        raise TemplateError(f"{where}.{key}: Farbe als RRGGBB (Großbuchstaben).")
    return value


def _fill(value: object, where: str) -> Fill:
    data = mapping_of(value, where)
    unknown = sorted(set(data) - {"if", "color", "bold"})
    if unknown:
        raise TemplateError(f"{where}: unbekannte Felder {unknown}.")
    return Fill(
        color_of(data, "color", where), condition_of(data, where), flag_of(data, "bold", where)
    )


def fills_of(data: Mapping[str, object], key: str, where: str) -> tuple[Fill, ...]:
    """``"RRGGBB"`` (always) or a list of ``{"if", "color", "bold"}`` rules."""
    value = data.get(key)
    if value is None:
        return ()
    if isinstance(value, str):
        return (Fill(color_of(data, key, where)),)
    rules = list_of(value, f"{where}.{key}")
    return tuple(_fill(rule, f"{where}.{key}[{i}]") for i, rule in enumerate(rules))


def _column(value: object, where: str) -> Column:
    data = mapping_of(value, where)
    align = text_of(data, "align", where, "left")
    if align not in ("left", "right", "center"):
        raise TemplateError(f"{where}.align: left, right oder center.")
    return Column(
        text_of(data, "header", where), text_of(data, "cell", where), align,
        _number(data, "width", where, 0, 100), flag_of(data, "bold", where),
        fills_of(data, "fill", where),
    )  # fmt: skip


def _table(data: Mapping[str, object], where: str, depth: int) -> Block:
    columns = list_of(data.get("columns"), f"{where}.columns")
    if not columns:
        raise TemplateError(f"{where}.columns: mindestens eine Spalte.")
    borders = text_of(data, "borders", where, "grid")
    if borders not in BORDERS:
        raise TemplateError(f"{where}.borders: {', '.join(BORDERS)}.")
    return Table(
        text_of(data, "source", where),
        tuple(_column(c, f"{where}.columns[{i}]") for i, c in enumerate(columns)),
        text_of(data, "as", where, "zeile"),
        condition_of(data, where),
        text_of(data, "empty", where, ""),
        flag_of(data, "header_if_empty", where),
        borders,
        color_of(data, "header_fill", where),
        color_of(data, "stripe", where),
        fills_of(data, "row_fill", where),
    )


def _fields(data: Mapping[str, object], where: str, depth: int) -> Block:
    rows = []
    for index, raw in enumerate(list_of(data.get("rows"), f"{where}.rows")):
        row = mapping_of(raw, f"{where}.rows[{index}]")
        rows.append(Field(text_of(row, "label", where), text_of(row, "value", where)))
    empty = data.get("empty")
    if empty is not None and not isinstance(empty, str):
        raise TemplateError(f"{where}.empty: Text erwartet.")
    return Fields(tuple(rows), condition_of(data, where), empty)


def _pagebreak(data: Mapping[str, object], where: str, depth: int) -> Block:
    return PageBreak(condition_of(data, where))


def _section(data: Mapping[str, object], where: str, depth: int) -> Block:
    repeat = data.get("for")
    if repeat is not None and not isinstance(repeat, str):
        raise TemplateError(f"{where}.for: Datenpfad erwartet.")
    level = data.get("level", 2)
    if level not in (1, 2, 3):
        raise TemplateError(f"{where}.level: 1, 2 oder 3.")
    return Section(
        parse_blocks(data.get("blocks"), f"{where}.blocks", depth + 1),
        text_of(data, "title", where, ""),
        condition_of(data, where),
        repeat,
        text_of(data, "as", where, "eintrag"),
        text_of(data, "id", where, ""),
        int(str(level)),
        anchor_of(data, "anchor", where),
    )


_PARSERS: dict[str, Callable[[Mapping[str, object], str, int], Block]] = {
    "heading": _heading,
    "paragraph": _paragraph,
    "textblock": _textblock,
    "list": _list,
    "table": _table,
    "fields": _fields,
    "pagebreak": _pagebreak,
    "section": _section,
    "image": _image,
    "toc": _contents,
}


def parse_blocks(value: object, where: str, depth: int = 0) -> tuple[Block, ...]:
    """Blocks of a JSON list; nesting deeper than :data:`MAX_BLOCK_DEPTH` is rejected."""
    if depth > MAX_BLOCK_DEPTH:
        raise TemplateError(f"{where}: Abschnitte zu tief verschachtelt.")
    blocks: list[Block] = []
    for index, raw in enumerate(list_of(value, where)):
        data = mapping_of(raw, f"{where}[{index}]")
        parser = _PARSERS.get(str(data.get("type")))
        if parser is None:
            raise TemplateError(f"{where}[{index}].type: erlaubt sind {', '.join(_PARSERS)}.")
        blocks.append(parser(data, f"{where}[{index}]", depth))
    return tuple(blocks)
