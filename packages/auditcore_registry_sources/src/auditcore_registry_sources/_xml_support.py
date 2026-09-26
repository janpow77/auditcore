"""Shared XML reading for the official sanctions lists: safe parsing, dates, identifiers."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal, TypeAlias
from xml.etree.ElementTree import Element  # noqa: S405 - type only; parsing uses defusedxml

from auditcore_common.safe_xml import parse_xml

from .errors import DependencyError

DateMode = Literal["legacy", "text"]
#: A value of a parser dictionary of the originals.
XmlValue: TypeAlias = str | date | list[str] | None
#: A parser dictionary of the originals (key sets differ per list).
XmlRecord: TypeAlias = dict[str, XmlValue]
EU_NAMESPACE = {"ns": "http://eu.europa.ec/fpi/fsd/export"}
_DATE_FORMATS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d.%m.%Y",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%d %b %Y",
    "%d %B %Y",
    "%Y",
)


def _fromstring(data: bytes) -> Element:
    return parse_xml(
        data,
        error=DependencyError,
        message="Für XML-Sanktionslisten ist 'auditcore_registry_sources[xml]' zu installieren.",
    )


def detect_namespace(root: Element) -> dict[str, str]:
    """Default namespace of the root element as ``{"ns": uri}`` (empty without one)."""
    tag = root.tag
    if tag.startswith("{"):
        return {"ns": tag[1 : tag.index("}")]}
    return {}


def _text(element: Element, tag: str, ns: dict[str, str] | None = None) -> str | None:
    child = element.find(tag, ns) if ns else element.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return None


def parse_date_legacy(value: str | None) -> date | None:
    """``_parse_date_safe`` of the originals: first matching format, else a leading year."""
    if not value:
        return None
    value = value.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    year = re.match(r"^(\d{4})", value)
    if year:
        try:
            return date(int(year.group(1)), 1, 1)
        except ValueError:
            pass
    return None


def _date(value: str | None, mode: DateMode) -> date | str | None:
    if mode == "legacy":
        return parse_date_legacy(value)
    return value.strip() if value and value.strip() else None


def _id_buckets(pairs: list[tuple[str, str, str]]) -> dict[str, list[str]]:
    """Sort identifiers like the originals: passport, tax, VAT, else registration."""
    buckets: dict[str, list[str]] = {"passport": [], "tax": [], "vat": [], "registration": []}
    for code, description, number in pairs:
        if not number:
            continue
        if "passport" in description or code == "passport":
            buckets["passport"].append(number)
        elif "tax" in description or "tin" in description:
            buckets["tax"].append(number)
        elif "vat" in description:
            buckets["vat"].append(number)
        else:
            buckets["registration"].append(number)
    return buckets


@dataclass(frozen=True)
class RecordExtra:
    """What the library reads beyond the originals: all birth dates, countries and addresses."""

    birth_dates: list[str]
    countries: list[str]
    addresses: list[str]
    schema_hint: str


@dataclass(frozen=True)
class ParsedRecord:
    """A parser dictionary of the originals with the library's additional values."""

    fields: XmlRecord
    extra: RecordExtra


#: Records and the ids of entries skipped for lack of a name.
ParseOutcome: TypeAlias = tuple[list[ParsedRecord], list[str]]


@dataclass
class AddressSummary:
    """First address as the originals read it, plus every country and address text."""

    country: str | None = None
    city: str | None = None
    address: str | None = None
    countries: list[str] = field(default_factory=list)
    addresses: list[str] = field(default_factory=list)

    def add(self, index: int, country: str | None, city: str | None, joined: str | None) -> None:
        """Record one address; only the first one fills country, city and address."""
        if index == 0:
            self.country, self.city, self.address = country, city, joined
        if country and country not in self.countries:
            self.countries.append(country)
        if joined:
            self.addresses.append(joined)


def join_present(parts: tuple[str | None, ...], separator: str = ", ") -> str | None:
    """Join the non-empty parts, ``None`` if there are none."""
    present = [p for p in parts if p]
    return separator.join(present) if present else None
