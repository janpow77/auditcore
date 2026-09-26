"""Official sanctions list XML: EU FSF (1.1), OFAC SDN and UN Security Council.

Ported from the free parser functions of the audit-portal (``audit_prep/
sanctions_xml.py``, absorbed from flowinvoice's ``SanctionsDownloader``); both
originals produce identical results on all recorded fixtures. Parsing uses
``defusedxml`` (extra ``xml``): the lists are large external documents and
entity expansion must not be possible.

Two date modes exist on purpose:

* ``dates="legacy"`` reproduces the originals: every date becomes a
  :class:`datetime.date`; a bare year ``1961`` becomes ``1961-01-01``.
* ``dates="text"`` (library default) keeps the spelling of the list, so a year
  of birth is not turned into a precise day.

Only the first address, birth date and nationality are read by the originals;
:func:`xml_entries` additionally collects all of them for screening
(``countries``/``birth_date`` joined with ``;``). Entries without a name are
reported as issues instead of disappearing.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable, Mapping
from datetime import date
from typing import cast

from ._xml_eu import parse_eu
from ._xml_ofac import parse_ofac
from ._xml_support import (
    EU_NAMESPACE,
    DateMode,
    ParseOutcome,
    XmlRecord,
    XmlValue,
    detect_namespace,
    parse_date_legacy,
)
from ._xml_un import parse_un
from .errors import DependencyError, FormatError
from .model import ListEntry, ParsedList, RowIssue
from .opensanctions_csv import PORTAL_COLUMNS, serialize_targets_simple_csv

__all__ = [
    "EU_NAMESPACE",
    "EXTRA",
    "FORMATS",
    "DateMode",
    "XmlRecord",
    "XmlValue",
    "detect_namespace",
    "parse_date_legacy",
    "parse_xml_list",
    "serialize_xml_list",
    "to_simple_row",
    "xml_entries",
]

FORMATS = ("eu_fsf_xml", "ofac_sdn_xml", "un_sc_xml")
#: Key under which 0.1.0 kept the additional values inside the parser dictionaries;
#: kept for compatibility, the values now travel separately (``RecordExtra``).
EXTRA = "__extra"

_PARSERS: dict[str, Callable[[bytes, DateMode], ParseOutcome]] = {
    "eu_fsf_xml": parse_eu,
    "ofac_sdn_xml": parse_ofac,
    "un_sc_xml": parse_un,
}


def parse_xml_list(data: bytes, format: str, *, dates: DateMode = "text") -> list[XmlRecord]:
    """Parser dictionaries of the originals (key sets differ per list).

    Raises the XML ``ParseError`` of the parser for malformed input, like the
    originals; :func:`xml_entries` wraps it into :class:`FormatError`.
    """
    if format not in _PARSERS:
        raise FormatError(f"Unbekanntes XML-Listenformat '{format}'.")
    records, _ = _PARSERS[format](data, dates)
    return [dict(r.fields) for r in records]


def _join(*lists: object) -> str:
    """Join optional lists with ``;``."""
    parts: list[str] = []
    for values in lists:
        if values:
            parts.extend(str(x).strip() for x in cast(Iterable[object], values) if str(x).strip())
    return ";".join(parts)


def _iso(value: object) -> str:
    """ISO text of a date, the text itself, or ``""``."""
    if isinstance(value, date):
        return value.isoformat()
    return value if isinstance(value, str) else ""


def to_simple_row(parsed: Mapping[str, object]) -> dict[str, str]:
    """Parser dictionary → OpenSanctions ``targets.simple.csv`` row (portal adapter)."""
    return {
        "id": str(parsed.get("list_id") or "").strip(),
        "schema": {"individual": "Person", "entity": "Organization"}.get(
            str(parsed.get("entity_type") or ""), ""
        ),
        "name": str(parsed.get("name") or "").strip(),
        "aliases": _join(parsed.get("aliases")),
        "birth_date": _iso(parsed.get("date_of_birth")),
        "countries": str(parsed.get("country") or "").strip(),
        "addresses": str(parsed.get("address") or "").strip(),
        "identifiers": _join(
            parsed.get("vat_ids"),
            parsed.get("tax_ids"),
            parsed.get("registration_numbers"),
            parsed.get("passport_numbers"),
        ),
        "sanctions": "",
        "program_ids": _join(parsed.get("sanction_programs")),
        "first_seen": _iso(parsed.get("listing_date")),
        "last_seen": "",
    }


def serialize_xml_list(parsed: list[XmlRecord]) -> bytes:
    """Portal-compatible ``targets.simple.csv`` bytes of parser dictionaries."""
    return serialize_targets_simple_csv((to_simple_row(p) for p in parsed), columns=PORTAL_COLUMNS)


def _parse_for_entries(data: bytes, format: str, list_key: str) -> ParseOutcome:
    if format not in _PARSERS:
        raise FormatError(f"Unbekanntes XML-Listenformat '{format}'.")
    try:
        return _PARSERS[format](data, "text")
    except DependencyError:
        raise
    except Exception as exc:  # noqa: BLE001 - every parser failure is a format error
        raise FormatError(f"XML-Liste '{list_key}' nicht lesbar: {exc}") from exc


def xml_entries(data: bytes, *, format: str, list_key: str) -> ParsedList:
    """Library contract: list entries with all birth dates/countries, skipped names as issues."""
    records, skipped = _parse_for_entries(data, format, list_key)
    entries: list[ListEntry] = []
    issues = [RowIssue(0, "Name fehlt", key or None) for key in skipped]
    for record in records:
        row = to_simple_row(record.fields)
        extra = record.extra
        aliases = record.fields.get("aliases")
        if not row["id"]:
            issues.append(RowIssue(0, "Kennung fehlt", None))
            continue
        entries.append(
            ListEntry(
                list_key=list_key,
                entry_id=row["id"],
                schema=row["schema"],
                name=row["name"],
                aliases=tuple(aliases) if isinstance(aliases, list) else (),
                birth_date=";".join(extra.birth_dates),
                countries=";".join(extra.countries),
                addresses="; ".join(extra.addresses),
                identifiers=row["identifiers"],
                sanctions="",
                program_ids=row["program_ids"],
                first_seen=row["first_seen"],
                last_seen="",
                dataset=format,
            )
        )
    if not entries:
        raise FormatError(f"XML-Liste '{list_key}' enthält keine verwertbaren Einträge.")
    return ParsedList(
        list_key=list_key,
        format=format,
        entries=tuple(entries),
        issues=tuple(issues),
        rows_seen=len(records) + len(skipped),
        columns=(),
        content_sha256=hashlib.sha256(data).hexdigest(),
    )
