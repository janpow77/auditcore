"""Resolve a structured template with data into a format-neutral document.

The resolved document holds only finished texts (no placeholders, no
conditions); DOCX, PDF and HTML renderers draw the same nodes, so all
formats show identical content.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from auditcore_common.hashing import canonical_sha256

from .conditions import Condition, evaluate
from .errors import Issue, RenderLimitError, TemplateDataError, TemplateError
from .model import (
    Block,
    BlockRef,
    BulletList,
    Fields,
    Fill,
    Heading,
    PageBreak,
    Paragraph,
    ReportTemplate,
    Section,
    Table,
)
from .placeholders import Scope, substitute
from .schema import validate
from .values import lookup, plain


@dataclass(frozen=True)
class ResolveLimits:
    """Upper bounds per document; exceeding one raises :class:`RenderLimitError`."""

    max_nodes: int = 20_000
    max_characters: int = 5_000_000
    max_loop_items: int = 10_000


@dataclass(frozen=True)
class RHeading:
    """Resolved heading."""

    text: str
    level: int


@dataclass(frozen=True)
class RParagraph:
    """Resolved paragraph; ``block`` names the text block it came from."""

    text: str
    block: str = ""


@dataclass(frozen=True)
class RList:
    """Resolved bullet list."""

    items: tuple[str, ...]


@dataclass(frozen=True)
class RTable:
    """Resolved table: header, alignment per column and body rows.

    Layout extras are empty for a plain table: ``widths`` (relative weights per
    column), ``fills``/``bold`` (per body cell, ``""``/``False`` = none),
    ``borders`` and ``header_fill`` (``""`` = design profile).
    """

    headers: tuple[str, ...]
    aligns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    widths: tuple[float, ...] = ()
    fills: tuple[tuple[str, ...], ...] = ()
    bold: tuple[tuple[bool, ...], ...] = ()
    borders: str = "grid"
    header_fill: str = ""


@dataclass(frozen=True)
class RFields:
    """Resolved key data."""

    rows: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class RPageBreak:
    """Resolved page break."""


Node = RHeading | RParagraph | RList | RTable | RFields | RPageBreak


@dataclass(frozen=True)
class ResolvedDocument:
    """Finished content plus provenance: template id, version, fingerprint and data hash."""

    title: str
    template_id: str
    template_version: str
    template_fingerprint: str
    data_sha256: str
    nodes: tuple[Node, ...]
    text_blocks: tuple[str, ...]
    #: Page orientation set by the template (``""`` = design profile decides).
    orientation: str = ""


class _Resolver:
    def __init__(self, template: ReportTemplate, limits: ResolveLimits) -> None:
        self.template = template
        self.limits = limits
        self.nodes: list[Node] = []
        self.used: list[str] = []
        self.characters = 0

    def emit(self, node: Node, size: int) -> None:
        self.nodes.append(node)
        self.characters += size
        if len(self.nodes) > self.limits.max_nodes:
            raise RenderLimitError(f"Mehr als {self.limits.max_nodes} Bausteine im Dokument.")
        if self.characters > self.limits.max_characters:
            raise RenderLimitError(f"Mehr als {self.limits.max_characters} Zeichen im Dokument.")

    def holds(self, condition: Condition | None, scope: Scope) -> bool:
        return condition is None or evaluate(condition, scope.values, self.template.conditions)

    def block_text(self, block_id: str, scope: Scope) -> str:
        block = self.template.text_block(block_id)
        if block is None:  # pragma: no cover - excluded by the checker
            raise TemplateError(f"Unbekannter Textbaustein {block_id!r}.")
        if not self.holds(block.condition, scope):
            return ""
        if block_id not in self.used:
            self.used.append(block_id)
        return substitute(block.text, scope, f"Textbaustein {block_id}")

    def items(self, source: str, scope: Scope) -> Sequence[object]:
        value = lookup(scope.values, source)
        entries = value if isinstance(value, (list, tuple)) else []
        if len(entries) > self.limits.max_loop_items:
            raise RenderLimitError(f"{source}: mehr als {self.limits.max_loop_items} Einträge.")
        return entries

    def text(self, text: str, scope: Scope, where: str) -> str:
        return substitute(text, scope, where)

    def block(self, block: Block, scope: Scope, where: str) -> None:
        if not isinstance(block, Section) and not self.holds(block.condition, scope):
            return
        if isinstance(block, Heading):
            text = self.text(block.text, scope, where)
            self.emit(RHeading(text, block.level), len(text))
        elif isinstance(block, Paragraph):
            self.paragraphs(self.text(block.text, scope, where), "")
        elif isinstance(block, BlockRef):
            self.paragraphs(self.block_text(block.block, scope), block.block)
        elif isinstance(block, (BulletList, Table)):
            self.listing(block, scope, where)
        elif isinstance(block, Fields):
            self.fields(block, scope, where)
        elif isinstance(block, PageBreak):
            self.emit(RPageBreak(), 0)
        else:
            self.section(block, scope, where)

    def paragraphs(self, text: str, block: str) -> None:
        for part in text.split("\n\n"):
            if part.strip():
                self.emit(RParagraph(part.strip("\n"), block), len(part))

    def listing(self, block: BulletList | Table, scope: Scope, where: str) -> None:
        entries = [scope.bind(block.var, entry) for entry in self.items(block.source, scope)]
        if not entries:
            if isinstance(block, Table) and block.header_if_empty:
                self.table(block, scope, entries, where)
            self.paragraphs(self.text(block.empty_text, scope, where), "")
        elif isinstance(block, BulletList):
            items = tuple(self.text(block.item, inner, where) for inner in entries)
            self.emit(RList(items), sum(map(len, items)))
        else:
            self.table(block, scope, entries, where)

    def table(self, block: Table, scope: Scope, entries: list[Scope], where: str) -> None:
        rows = tuple(
            tuple(self.text(c.cell, inner, where) for c in block.columns) for inner in entries
        )
        headers = tuple(self.text(c.header, scope, where) for c in block.columns)
        aligns = tuple(c.align for c in block.columns)
        widths = tuple(c.width or 1.0 for c in block.columns)
        styled = (
            [self.cell_styles(block, i, inner) for i, inner in enumerate(entries)]
            if block.styled
            else []
        )
        node = RTable(
            headers, aligns, rows,
            widths if any(c.width for c in block.columns) else (),
            tuple(tuple(color for color, _ in row) for row in styled),
            tuple(tuple(bold for _, bold in row) for row in styled),
            block.borders, block.header_fill,
        )  # fmt: skip
        self.emit(node, sum(len(cell) for row in rows for cell in row))

    def first(self, fills: tuple[Fill, ...], scope: Scope) -> Fill | None:
        return next((fill for fill in fills if self.holds(fill.condition, scope)), None)

    def cell_styles(self, block: Table, index: int, scope: Scope) -> tuple[tuple[str, bool], ...]:
        """Colour and emphasis per cell: cell rule, then row rule, then stripe."""
        row = self.first(block.row_fills, scope) or Fill()
        stripe = block.stripe if index % 2 == 1 else ""
        cells = []
        for column in block.columns:
            cell = self.first(column.fills, scope) or Fill()
            color = cell.color or row.color or stripe
            cells.append((color, column.bold or cell.bold or row.bold))
        return tuple(cells)

    def fields(self, block: Fields, scope: Scope, where: str) -> None:
        rows = []
        for row in block.rows:
            value = self.text(row.value, scope, where)
            if not value.strip() and block.empty is not None:
                value = self.text(block.empty, scope, where)
            if value.strip() or block.empty is not None:
                rows.append((self.text(row.label, scope, where), value))
        if rows:
            self.emit(RFields(tuple(rows)), sum(len(label) + len(v) for label, v in rows))

    def section(self, block: Section, scope: Scope, where: str) -> None:
        scopes = [scope]
        if block.repeat is not None:
            scopes = [scope.bind(block.var, entry) for entry in self.items(block.repeat, scope)]
        for inner in scopes:
            if not self.holds(block.condition, inner):
                continue
            if block.title:
                title = self.text(block.title, inner, where)
                self.emit(RHeading(title, block.level), len(title))
            for index, child in enumerate(block.blocks):
                self.block(child, inner, f"{where}.blocks[{index}]")


def checked_data(template: ReportTemplate, data: object) -> Mapping[str, object]:
    """``data`` if it satisfies the template's JSON schema, else :class:`TemplateDataError`."""
    issues = validate(data, template.schema)
    if issues:
        raise TemplateDataError(issues)
    if not isinstance(data, Mapping):
        raise TemplateDataError((Issue("$", "JSON-Objekt erwartet"),))
    return data


def resolve(
    template: ReportTemplate, data: object, limits: ResolveLimits | None = None
) -> ResolvedDocument:
    """Validate ``data`` against the data contract and resolve all blocks."""
    if template.docx is not None:
        raise TemplateError(
            f"{template.id}: DOCX-Vorlagen werden mit render_docx_template gefüllt."
        )
    values = checked_data(template, plain(data))
    resolver = _Resolver(template, limits or ResolveLimits())
    scope = Scope(values, resolver.block_text)
    for index, block in enumerate(template.blocks):
        resolver.block(block, scope, f"blocks[{index}]")
    return ResolvedDocument(
        resolver.text(template.title, scope, "title"),
        template.id,
        template.version,
        template.fingerprint,
        canonical_sha256(values),
        tuple(resolver.nodes),
        tuple(resolver.used),
        template.orientation,
    )
