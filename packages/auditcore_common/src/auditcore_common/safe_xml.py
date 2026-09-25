"""XML parsing only through ``defusedxml`` (extra ``xml``), imported lazily."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

# Type only; parsing uses defusedxml.
from xml.etree.ElementTree import Element  # nosec B405


class FromString(Protocol):
    """``defusedxml.ElementTree.fromstring``."""

    def __call__(self, text: bytes | str, *, forbid_dtd: bool = ...) -> Element:
        """Parse a document into its root element."""
        ...


def defused_fromstring(error: Callable[[str], Exception], message: str) -> FromString:
    """``defusedxml.ElementTree.fromstring`` or ``error(message)`` without the extra.

    Separate from :func:`parse_xml` for callers that turn parse failures into
    their own error but must keep a missing dependency distinguishable.
    """
    try:
        from defusedxml.ElementTree import fromstring
    except ImportError as exc:
        raise error(message) from exc
    parser: FromString = fromstring
    return parser


def parse_xml(
    data: bytes | str,
    *,
    error: Callable[[str], Exception],
    message: str,
    forbid_dtd: bool = False,
) -> Element:
    """Root element of ``data`` parsed with ``defusedxml``; parse errors propagate."""
    return defused_fromstring(error, message)(data, forbid_dtd=forbid_dtd)
