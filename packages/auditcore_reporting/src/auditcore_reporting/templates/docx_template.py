"""Fill Word templates (DOCX/DOTX) with placeholders and control tags (extra ``docx``).

The Word file carries the authority's corporate design (letterhead, styles,
header, footer); the library only replaces ``{{ … }}`` placeholders and
expands ``{%p … %}``/``{%tr … %}`` tags. Before anything is read the package
passes the security check of :mod:`._docx_package`; XML is parsed through
``auditcore_common.safe_xml`` (defusedxml, DTDs forbidden). Placeholders
that Word split over several runs are joined; the formatting of the first
run of a placeholder is kept.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from xml.etree.ElementTree import Element  # nosec B405 - tree only; parsing is defused

from . import _wordml
from ._docx_package import MAIN_DOCUMENT, MAIN_TEMPLATE, DocxLimits, read_package
from ._docx_walk import walk
from ._docx_xml import BR, XML_NS, P, Part, own_texts, paragraph_text
from .checker import Bindings, Checker
from .conditions import evaluate
from .errors import RenderLimitError, TemplateError
from .model import ReportTemplate
from .placeholders import BLOCK_ROOT, PLACEHOLDER, Scope, parse_placeholder, placeholders
from .resolve import ResolveLimits, checked_data
from .values import format_value, lookup, plain

_BODY_PARTS = re.compile(r"word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml")
_SPACE = f"{{{XML_NS}}}space"


class _CheckVisitor:
    def __init__(self, checker: Checker) -> None:
        self.checker = checker
        self.placeholders: list[str] = []

    def when(self, name: str, negate: bool, context: Bindings, where: str) -> list[Bindings]:
        self.checker.condition(name, context, where)
        return [context]

    def each(self, var: str, path: str, context: Bindings, where: str) -> list[Bindings]:
        return [self.checker.loop(path, var, context, where)]

    def fill(self, paragraph: Element, texts: list[Element], context: Bindings, where: str) -> bool:
        text = "".join(t.text or "" for t in texts)
        self.checker.text(text, context, where)
        self.placeholders.extend(p.path for p in placeholders(text, where))
        return True


class _RenderVisitor:
    def __init__(self, template: ReportTemplate, limits: ResolveLimits) -> None:
        self.template = template
        self.limits = limits
        self.paragraphs = 0

    def when(self, name: str, negate: bool, context: Scope, where: str) -> list[Scope]:
        holds = evaluate(name, context.values, self.template.conditions)
        return [context] if holds != negate else []

    def each(self, var: str, path: str, context: Scope, where: str) -> list[Scope]:
        value = lookup(context.values, path)
        items = value if isinstance(value, list) else []
        if len(items) > self.limits.max_loop_items:
            raise RenderLimitError(f"{path}: mehr als {self.limits.max_loop_items} Einträge.")
        return [context.bind(var, item) for item in items]

    def value(self, expression: str, context: Scope, where: str) -> str:
        placeholder = parse_placeholder(expression, where)
        if placeholder.block is not None:
            return context.block_text(placeholder.block, context)
        return format_value(lookup(context.values, placeholder.path), placeholder.filter, where)

    def fill(self, paragraph: Element, texts: list[Element], context: Scope, where: str) -> bool:
        self.paragraphs += 1
        if self.paragraphs > self.limits.max_nodes:
            raise RenderLimitError(f"Mehr als {self.limits.max_nodes} Absätze im Dokument.")
        full = "".join(t.text or "" for t in texts)
        if "{{" not in full:
            return True
        only_block = re.fullmatch(r"\s*\{\{\s*" + BLOCK_ROOT + r"\.[^{}]*\}\}\s*", full) is not None
        _replace(texts, full, lambda expression: self.value(expression, context, where))
        _line_breaks(paragraph, texts)
        return not (only_block and not paragraph_text(paragraph).strip())


def _replace(texts: list[Element], full: str, render: Callable[[str], str]) -> None:
    """Replace placeholders spanning several ``w:t`` from the end backwards."""
    starts, offset = [], 0
    for node in texts:
        starts.append(offset)
        offset += len(node.text or "")
    for match in reversed(list(PLACEHOLDER.finditer(full))):
        start, end = match.span()
        first = max(i for i, s in enumerate(starts) if s <= start)
        last = max(i for i, s in enumerate(starts) if s <= end - 1)
        head = (texts[first].text or "")[: start - starts[first]]
        tail = (texts[last].text or "")[end - starts[last] :]
        value = render(match.group(1))
        for index in range(first + 1, last + 1):
            texts[index].text = ""
        texts[first].text = head + value + (tail if first == last else "")
        if first != last:
            texts[last].text = tail
        for index in range(first, last + 1):
            texts[index].set(_SPACE, "preserve")


def _line_breaks(paragraph: Element, texts: list[Element]) -> None:
    """``\\n`` in inserted values becomes ``w:br`` inside the same run."""
    parents = {child: parent for parent in paragraph.iter() for child in parent}
    for node in texts:
        if "\n" not in (node.text or ""):
            continue
        run = parents[node]
        position = list(run).index(node)
        lines = (node.text or "").split("\n")
        node.text = lines[0]
        for offset, line in enumerate(lines[1:], start=1):
            extra = Element(node.tag, {_SPACE: "preserve"})
            extra.text = line
            run.insert(position + 2 * offset - 1, Element(BR))
            run.insert(position + 2 * offset, extra)


@dataclass(frozen=True)
class DocxInspection:
    """What a checked DOCX template reads: placeholders and whether it is a DOTX."""

    placeholders: tuple[str, ...]
    template: bool


def check_docx_template(
    data: bytes, checker: Checker, limits: DocxLimits | None = None
) -> DocxInspection:
    """Security check plus static check of all placeholders and tags against the schema."""
    package = read_package(data, limits)
    visitor = _CheckVisitor(checker)
    for name, raw in package.entries:
        if _BODY_PARTS.fullmatch(name):
            walk(Part(name, raw).root, visitor, {}, name)
    return DocxInspection(tuple(dict.fromkeys(visitor.placeholders)), package.template)


def render_docx_template(
    template: ReportTemplate, data: object, limits: ResolveLimits | None = None
) -> bytes:
    """Filled DOCX (a DOTX becomes a DOCX); identical input gives identical bytes."""
    if template.docx is None:
        raise TemplateError(f"{template.id}: keine DOCX-Vorlage; render_docx verwenden.")
    package = read_package(template.docx)
    values = checked_data(template, plain(data))
    visitor = _RenderVisitor(template, limits or ResolveLimits())

    def block_text(block_id: str, scope: Scope) -> str:
        block = template.text_block(block_id)
        if block is None or (
            block.condition is not None
            and not evaluate(block.condition, scope.values, template.conditions)
        ):
            return ""
        return _fill_block(block.text, scope, visitor, block_id)

    scope = Scope(values, block_text)
    entries: list[tuple[str, bytes]] = []
    for name, raw in package.entries:
        if _BODY_PARTS.fullmatch(name):
            part = Part(name, raw)
            walk(part.root, visitor, scope, name)
            raw = part.to_bytes()
        elif name == "[Content_Types].xml" and package.template:
            raw = raw.replace(MAIN_TEMPLATE.encode(), MAIN_DOCUMENT.encode())
        entries.append((name, raw))
    return _wordml.write_zip(entries)


def _fill_block(text: str, scope: Scope, visitor: _RenderVisitor, block_id: str) -> str:
    return PLACEHOLDER.sub(
        lambda m: visitor.value(m.group(1), scope, f"Textbaustein {block_id}"), text
    )


def docx_paragraphs(data: bytes) -> tuple[str, ...]:
    """Paragraph texts of ``word/document.xml`` (text preview of a filled template)."""
    package = read_package(data)
    root = Part("word/document.xml", package.get("word/document.xml") or b"").root
    return tuple("".join(t.text or "" for t in own_texts(p)[0]) for p in root.iter(P))
