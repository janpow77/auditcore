"""Anchor links of HTML pages and HTML marker detection (standard library only)."""

from __future__ import annotations

from collections.abc import Sequence
from html.parser import HTMLParser

#: Markers of a complete HTML document.
DOCUMENT_MARKERS = ("<html", "<!doctype")


class LinkCollector(HTMLParser):
    """Collect ``(href, text)`` of every ``<a href>``; text whitespace is collapsed.

    An anchor without (or with an empty) ``href`` is ignored; a new anchor
    start replaces an unfinished one.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Start collecting the text of an anchor with ``href``."""
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self._href, self._text = href, []

    def handle_data(self, data: str) -> None:
        """Collect anchor text."""
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        """Finish the current anchor."""
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join("".join(self._text).split())))
            self._href = None


def anchor_links(html: str) -> list[tuple[str, str]]:
    """``(href, text)`` of the anchors of ``html`` as :class:`LinkCollector` reads them."""
    parser = LinkCollector()
    parser.feed(html)
    return parser.links


def has_html_marker(
    text: str, markers: Sequence[str] = DOCUMENT_MARKERS, *, window: int | None = 4096
) -> bool:
    """True if a lower-case marker occurs in the first ``window`` characters (all if ``None``).

    The window is cut before lower-casing, as in the sources.
    """
    head = (text if window is None else text[:window]).lower()
    return any(marker in head for marker in markers)
