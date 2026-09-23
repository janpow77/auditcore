"""Standard-library HTML text and link extraction with BeautifulSoup semantics.

``page_text(doc)`` equals ``BeautifulSoup(doc, "html.parser").get_text(" ")``
for the characterized pages: text nodes joined with a single space, without
script/style/template contents, comments, doctype or processing
instructions. ``links(doc)`` equals ``[a["href"] for a in
soup.find_all("a", href=True)]``. The replay tests compare both against the
recorded BeautifulSoup 4.12.3 results.
"""

from __future__ import annotations

from html.parser import HTMLParser

_SKIP = {"script", "style", "template"}


class _Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.texts: list[str] = []
        self.hrefs: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIP:
            self._skip += 1
        if tag == "a":
            found: str | None = None
            present = False
            for name, value in attrs:
                if name == "href":
                    present, found = True, value or ""
            if present and found is not None:
                self.hrefs.append(found)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip and data:
            self.texts.append(data)


def _collect(doc: str) -> _Collector:
    parser = _Collector()
    parser.feed(doc)
    parser.close()
    return parser


def page_text(doc: str) -> str:
    """Visible text joined with single spaces (``get_text(" ")``)."""
    return " ".join(_collect(doc).texts)


def links(doc: str) -> list[str]:
    """``href`` values of all ``<a>`` elements in document order."""
    return _collect(doc).hrefs
