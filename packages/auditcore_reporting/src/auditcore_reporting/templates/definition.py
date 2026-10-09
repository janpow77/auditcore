"""Build a checked, fingerprinted :class:`ReportTemplate` from its JSON definition."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from typing import cast

from auditcore_common.frozen import freeze
from auditcore_common.hashing import canonical_sha256

from .blocks import condition_of, list_of, mapping_of, parse_blocks, text_of
from .checker import Bindings, Checker
from .conditions import Condition, condition_paths
from .errors import TemplateError
from .model import (
    FORMATS,
    STATUSES,
    Block,
    BlockRef,
    BulletList,
    Fields,
    Heading,
    Paragraph,
    ReportTemplate,
    Section,
    Table,
    TextBlock,
)
from .placeholders import PLACEHOLDER
from .schema import check_schema, validate

TEMPLATE_ID = re.compile(r"[a-z][a-z0-9-]{1,63}")
VERSION = re.compile(r"(0|[1-9]\d{0,3})\.(0|[1-9]\d{0,4})\.(0|[1-9]\d{0,5})")
_BLOCK_ID = re.compile(r"[A-Za-z_][A-Za-z0-9_-]{0,63}")
_KEYS = frozenset(
    {"id", "version", "name", "title", "description", "status", "schema", "conditions",
     "text_blocks", "blocks", "sample", "formats"}
)  # fmt: skip


def _frozen(value: Mapping[str, object]) -> Mapping[str, object]:
    """Read-only deep copy (``MappingProxyType``/``tuple``)."""
    frozen = freeze(dict(value))
    assert isinstance(frozen, Mapping)
    return frozen


def _text_block(value: object, where: str) -> TextBlock:
    data = mapping_of(value, where)
    block_id = text_of(data, "id", where)
    if not _BLOCK_ID.fullmatch(block_id):
        raise TemplateError(f"{where}.id: ungültige Kennung {block_id!r}.")
    text = text_of(data, "text", where)
    if "textbaustein." in text:
        raise TemplateError(f"{where}: Textbausteine dürfen keine Textbausteine enthalten.")
    required = data.get("required", False)
    if not isinstance(required, bool):
        raise TemplateError(f"{where}.required: true oder false.")
    return TextBlock(
        block_id,
        text,
        text_of(data, "title", where, ""),
        condition_of(data, where),
        required,
        text_of(data, "legal_basis", where, ""),
    )


def _text_blocks(value: object) -> tuple[TextBlock, ...]:
    blocks = tuple(
        _text_block(v, f"text_blocks[{i}]") for i, v in enumerate(list_of(value, "text_blocks"))
    )
    ids = [block.id for block in blocks]
    if len(set(ids)) != len(ids):
        raise TemplateError("text_blocks: doppelte Kennungen.")
    return blocks


def _conditions(value: object) -> dict[str, Condition]:
    named: dict[str, Condition] = {}
    for name, spec in mapping_of(value, "conditions").items():
        if not _BLOCK_ID.fullmatch(name) or not isinstance(spec, (str, Mapping)):
            raise TemplateError(f"conditions.{name}: Name und Bedingung prüfen.")
        named[name] = spec
    for name, spec in named.items():
        list(condition_paths(spec, named, f"conditions.{name}"))
    return named


def _check_listing(
    block: BulletList | Table, checker: Checker, bindings: Bindings, where: str
) -> None:
    inner = checker.loop(block.source, block.var, bindings, where)
    checker.text(block.empty_text, bindings, where)
    texts = [block.item] if isinstance(block, BulletList) else [c.cell for c in block.columns]
    for text in texts:
        checker.text(text, inner, where)


def _check_section(block: Section, checker: Checker, bindings: Bindings, where: str) -> None:
    inner = bindings
    if block.repeat is not None:
        inner = checker.loop(block.repeat, block.var, bindings, where)
    checker.condition(block.condition, inner, where)
    checker.text(block.title, inner, where)
    for index, child in enumerate(block.blocks):
        _check_block(child, checker, inner, f"{where}.blocks[{index}]")


def _check_block(block: Block, checker: Checker, bindings: Bindings, where: str) -> None:
    if isinstance(block, Section):
        _check_section(block, checker, bindings, where)
        return
    checker.condition(block.condition, bindings, where)
    if isinstance(block, (Heading, Paragraph)):
        checker.text(block.text, bindings, where)
    elif isinstance(block, BlockRef):
        checker.block_ref(block.block, bindings, where)
    elif isinstance(block, (BulletList, Table)):
        _check_listing(block, checker, bindings, where)
    elif isinstance(block, Fields):
        checker.text(block.empty or "", bindings, where)
        for row in block.rows:
            checker.text(row.label, bindings, where)
            checker.text(row.value, bindings, where)


def _name(data: Mapping[str, object]) -> str:
    """Display name: ``name`` or the title without placeholders."""
    name = text_of(data, "name", "Vorlage", "")
    if "{{" in name or "{%" in name:
        raise TemplateError("name: Anzeigename ohne Platzhalter.")
    title = PLACEHOLDER.sub("", text_of(data, "title", "Vorlage"))
    return name.strip() or " ".join(title.split()).strip(" –-") or text_of(data, "id", "Vorlage")


def _formats(value: object, docx: bytes | None) -> tuple[str, ...]:
    default = ("docx",) if docx is not None else FORMATS
    formats = tuple(str(v) for v in list_of(value, "formats")) if value is not None else default
    if not formats or not set(formats) <= set(default):
        raise TemplateError(f"formats: erlaubt sind {', '.join(default)}.")
    return formats


def _head(data: Mapping[str, object]) -> tuple[str, str, str]:
    unknown = sorted(set(data) - _KEYS)
    if unknown:
        raise TemplateError(f"Vorlage: unbekannte Felder {unknown}.")
    template_id, version = text_of(data, "id", "Vorlage"), text_of(data, "version", "Vorlage")
    if not TEMPLATE_ID.fullmatch(template_id):
        raise TemplateError(f"id: {template_id!r} (klein, a-z, 0-9, Bindestrich).")
    if not VERSION.fullmatch(version):
        raise TemplateError(f"version: {version!r} ist keine Version MAJOR.MINOR.PATCH.")
    status = text_of(data, "status", "Vorlage", "Entwurf")
    if status not in STATUSES:
        raise TemplateError(f"status: erlaubt sind {', '.join(STATUSES)}.")
    return template_id, version, status


def define_template(
    definition: Mapping[str, object], *, docx: bytes | None = None
) -> ReportTemplate:
    """Checked template: schema subset, blocks, placeholders, conditions, sample data.

    With ``docx`` the Word file is the body (security check, placeholders and
    tags checked against the schema); ``blocks`` must then be absent.
    """
    data = mapping_of(definition, "Vorlage")
    template_id, version, status = _head(data)
    schema = mapping_of(data.get("schema"), "schema")
    check_schema(schema)
    conditions = _conditions(data.get("conditions", {}))
    text_blocks = _text_blocks(data.get("text_blocks", []))
    checker = Checker(schema, conditions, text_blocks)
    checker.text(text_of(data, "title", "Vorlage"), {}, "title")
    blocks = _body(data, docx, checker)
    checker.finish()
    sample = mapping_of(data.get("sample", {}), "sample")
    issues = validate(sample, schema)
    if issues:
        raise TemplateError(f"sample: {issues[0].path}: {issues[0].message}.")
    docx_hash = hashlib.sha256(docx).hexdigest() if docx is not None else None
    fingerprint = canonical_sha256({"definition": data, "docx_sha256": docx_hash})
    return ReportTemplate(
        template_id,
        version,
        text_of(data, "title", "Vorlage"),
        text_of(data, "description", "Vorlage", ""),
        _frozen(schema),
        blocks,
        text_blocks,
        cast("Mapping[str, Condition]", _frozen(conditions)),
        _formats(data.get("formats"), docx),
        status,
        _frozen(sample),
        fingerprint,
        _frozen(data),
        docx,
        _name(data),
    )


def _body(data: Mapping[str, object], docx: bytes | None, checker: Checker) -> tuple[Block, ...]:
    if docx is None:
        blocks = parse_blocks(data.get("blocks"), "blocks")
        for index, block in enumerate(blocks):
            _check_block(block, checker, {}, f"blocks[{index}]")
        return blocks
    if "blocks" in data:
        raise TemplateError("Vorlage: 'blocks' und DOCX-Vorlage schließen sich aus.")
    from .docx_template import check_docx_template

    check_docx_template(docx, checker)
    return ()
