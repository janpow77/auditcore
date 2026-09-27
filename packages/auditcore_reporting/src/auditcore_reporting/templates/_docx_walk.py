"""Walk a WordprocessingML tree: control tags, loops, conditions and placeholders.

Control tags follow the docxtpl conventions (paragraph ``{%p … %}`` and table
row ``{%tr … %}``) but only a fixed grammar is accepted – no expressions::

    {%p if NAME %}  {%p if not NAME %}  {%p endif %}
    {%p for VAR in PATH %}  {%p endfor %}
    {%tr … %}  as the only text of a table row repeats or drops whole rows

``NAME`` is a named condition of the template or a data path. A tag must be
the only text of its paragraph (or row). The same walk serves the static
check (:class:`Visitor` of the checker) and the rendering.
"""

from __future__ import annotations

import copy
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar
from xml.etree.ElementTree import Element  # nosec B405 - tree only; parsing is defused

from ._docx_xml import BODY, SDT_CONTENT, TBL, TC, TR, TXBX, P, all_text, own_texts, q
from .errors import TemplateError

C = TypeVar("C")
_TAG = re.compile(r"\{%(p|tr)?\s+(.*?)\s*%\}", re.DOTALL)
_IF = re.compile(r"if\s+(not\s+)?([A-Za-z_][\w.-]*)")
_FOR = re.compile(r"for\s+([A-Za-z_]\w*)\s+in\s+([A-Za-z_][\w.]*)")
_CONTAINERS = frozenset({BODY, TC, TXBX, SDT_CONTENT, TBL, q("hdr"), q("ftr")})


@dataclass(frozen=True)
class Tag:
    """A parsed control tag."""

    level: str  # "p" or "tr"
    kind: str  # "if", "for", "endif", "endfor"
    name: str = ""
    negate: bool = False
    var: str = ""


class Visitor(Protocol[C]):
    """Checking or rendering behaviour plugged into the walk."""

    def when(self, name: str, negate: bool, context: C, where: str) -> list[C]:
        """Contexts for the body of ``if`` (none, one)."""
        ...

    def each(self, var: str, path: str, context: C, where: str) -> list[C]:
        """Contexts for the body of ``for`` (one per item)."""
        ...

    def fill(self, paragraph: Element, texts: list[Element], context: C, where: str) -> bool:
        """Replace placeholders; ``False`` removes the paragraph."""
        ...


def parse_tag(text: str, where: str) -> Tag | None:
    """Tag if ``text`` (stripped) is exactly one control tag; errors for stray tags."""
    stripped = text.strip()
    match = _TAG.fullmatch(stripped)
    if match is None:
        if "{%" in text or "%}" in text:
            raise TemplateError(
                f"{where}: Steuer-Tag muss allein im Absatz stehen ({stripped[:60]!r})."
            )
        return None
    level, body = match.group(1) or "p", match.group(2)
    if body in ("endif", "endfor"):
        return Tag(level, body)
    condition = _IF.fullmatch(body)
    if condition:
        return Tag(level, "if", condition.group(2), bool(condition.group(1)))
    loop = _FOR.fullmatch(body)
    if loop:
        return Tag(level, "for", loop.group(2), var=loop.group(1))
    raise TemplateError(f"{where}: unbekannter Steuer-Tag {stripped!r}.")


class Walker(Generic[C]):
    """Expands tags container by container; each unit is processed exactly once."""

    def __init__(self, visitor: Visitor[C], part: str) -> None:
        self.visitor = visitor
        self.part = part

    def where(self, element: Element) -> str:
        return f"{self.part} „{all_text(element).strip()[:40]}“"

    def unit_tag(self, unit: Element, in_table: bool) -> Tag | None:
        if in_table:
            text = all_text(unit).strip() if unit.tag == TR else ""
            return parse_tag(text, self.where(unit)) if text.startswith("{%tr") else None
        if unit.tag != P:
            return None
        tag = parse_tag("".join(t.text or "" for t in own_texts(unit)[0]), self.where(unit))
        if tag is not None and tag.level == "tr":
            raise TemplateError(
                f"{self.where(unit)}: tr-Tag muss allein in einer Tabellenzeile stehen."
            )
        return tag

    def container(self, element: Element, context: C) -> None:
        in_table = element.tag == TBL
        units = list(element)
        for unit in units:
            element.remove(unit)
        for unit in self.expand(units, in_table, context):
            element.append(unit)
        if element.tag == TC and not any(child.tag == P for child in element):
            element.append(Element(P))

    def expand(self, units: Sequence[Element], in_table: bool, context: C) -> list[Element]:
        result: list[Element] = []
        index = 0
        while index < len(units):
            unit = units[index]
            tag = self.unit_tag(unit, in_table)
            if tag is None:
                if self.element(unit, context):
                    result.append(unit)
                index += 1
                continue
            if tag.kind not in ("if", "for"):
                raise TemplateError(f"{self.where(unit)}: {tag.kind} ohne öffnenden Tag.")
            end = self.closing(units, index, in_table, tag)
            result.extend(self.branch(tag, units[index + 1 : end], in_table, context, unit))
            index = end + 1
        return result

    def closing(self, units: Sequence[Element], start: int, in_table: bool, tag: Tag) -> int:
        stack = [tag]
        for index in range(start + 1, len(units)):
            inner = self.unit_tag(units[index], in_table)
            if inner is None:
                continue
            if inner.kind in ("if", "for"):
                stack.append(inner)
            elif inner.kind != "end" + stack.pop().kind:
                raise TemplateError(f"{self.where(units[index])}: {inner.kind} passt nicht.")
            if not stack:
                return index
        raise TemplateError(f"{self.where(units[start])}: {tag.kind} ohne Ende-Tag.")

    def branch(self, tag: Tag, body: Sequence[Element], in_table: bool, context: C,
               unit: Element) -> list[Element]:  # fmt: skip
        where = self.where(unit)
        contexts = (
            self.visitor.when(tag.name, tag.negate, context, where)
            if tag.kind == "if"
            else self.visitor.each(tag.var, tag.name, context, where)
        )
        result: list[Element] = []
        for inner in contexts:
            result.extend(self.expand([copy.deepcopy(e) for e in body], in_table, inner))
        return result

    def element(self, element: Element, context: C) -> bool:
        """Process one unit; ``False`` drops it."""
        if element.tag == P:
            texts, boxes = own_texts(element)
            for box in boxes:
                self.container(box, context)
            return self.visitor.fill(element, texts, context, self.where(element))
        if element.tag in _CONTAINERS:
            self.container(element, context)
        else:
            for child in list(element):
                if not self.element(child, context):
                    element.remove(child)
        return True


def walk(root: Element, visitor: Visitor[C], context: C, part: str) -> None:
    """Process a part's root (``w:document``, ``w:hdr`` or ``w:ftr``)."""
    Walker(visitor, part).element(root, context)
