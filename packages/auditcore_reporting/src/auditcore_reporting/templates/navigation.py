"""Jump targets, internal links, table of contents and PDF outline.

Anchors are declared on headings and sections (``"anchor"``); a paragraph
with ``"link"`` jumps to one of them. Links are checked when the template is
defined. A table of contents (block ``toc``) or ``"outline": true`` gives
every heading a target: declared anchors are kept, the others are numbered
``auto-1``, ``auto-2`` … in document order. Templates without these keys
resolve exactly as before (no anchors, no bookmarks).
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence

from .errors import TemplateError
from .model import Block, Contents, Heading, Paragraph, Section


def _walk(blocks: Sequence[Block]) -> Iterator[Block]:
    for block in blocks:
        yield block
        if isinstance(block, Section):
            yield from _walk(block.blocks)


def check_navigation(blocks: Sequence[Block]) -> None:
    """Anchors are unique and every link points to a declared anchor."""
    anchors: list[str] = [
        block.anchor
        for block in _walk(blocks)
        if isinstance(block, (Heading, Section)) and block.anchor
    ]
    duplicates = sorted({a for a in anchors if anchors.count(a) > 1})
    if duplicates:
        raise TemplateError(f"Sprungmarken mehrfach vergeben: {duplicates}.")
    for block in _walk(blocks):
        if isinstance(block, Paragraph) and block.link and block.link not in anchors:
            raise TemplateError(f"link: Sprungmarke {block.link!r} ist nicht deklariert.")


def needs_targets(blocks: Sequence[Block], outline: bool) -> bool:
    """Whether every heading needs a target (table of contents or PDF outline)."""
    return outline or any(isinstance(block, Contents) for block in _walk(blocks))
