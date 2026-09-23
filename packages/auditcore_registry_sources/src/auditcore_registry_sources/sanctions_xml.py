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
import re
from collections.abc import Callable
from datetime import date, datetime
from typing import Any, Literal
from xml.etree.ElementTree import Element  # noqa: S405 - type only; parsing uses defusedxml

from .errors import DependencyError, FormatError
from .model import ListEntry, ParsedList, RowIssue
from .opensanctions_csv import PORTAL_COLUMNS, serialize_targets_simple_csv

DateMode = Literal["legacy", "text"]
EU_NAMESPACE = {"ns": "http://eu.europa.ec/fpi/fsd/export"}
FORMATS = ("eu_fsf_xml", "ofac_sdn_xml", "un_sc_xml")
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
EXTRA = "__extra"


def _fromstring(data: bytes) -> Element:
    try:
        from defusedxml.ElementTree import fromstring
    except ImportError as exc:  # pragma: no cover - exercised in the installed smoke test
        raise DependencyError(
            "Für XML-Sanktionslisten ist 'auditcore_registry_sources[xml]' zu installieren."
        ) from exc
    root: Element = fromstring(data)
    return root


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


def _parse_ofac(data: bytes, mode: DateMode) -> tuple[list[dict[str, Any]], list[str]]:
    root = _fromstring(data)
    ns = detect_namespace(root)
    records: list[dict[str, Any]] = []
    skipped: list[str] = []
    for entry in root.findall("ns:sdnEntry", ns):
        uid = _text(entry, "ns:uid", ns)
        sdn_type = _text(entry, "ns:sdnType", ns) or ""
        parts = [
            p for p in (_text(entry, "ns:firstName", ns), _text(entry, "ns:lastName", ns)) if p
        ]
        name = " ".join(parts)
        if not name:
            skipped.append(uid or "")
            continue
        programs = []
        program_list = entry.find("ns:programList", ns)
        if program_list is not None:
            programs = [
                p.text.strip()
                for p in program_list.findall("ns:program", ns)
                if p.text and p.text.strip()
            ]
        pairs = []
        id_list = entry.find("ns:idList", ns)
        if id_list is not None:
            for item in id_list.findall("ns:id", ns):
                kind = (_text(item, "ns:idType", ns) or "").lower()
                number = _text(item, "ns:idNumber", ns) or ""
                # The source never matches "passport" by code; only the type text counts.
                pairs.append(("", kind, number))
        buckets = _id_buckets(pairs)
        aliases = []
        aka_list = entry.find("ns:akaList", ns)
        if aka_list is not None:
            for aka in aka_list.findall("ns:aka", ns):
                alias = " ".join(
                    p for p in (_text(aka, "ns:firstName", ns), _text(aka, "ns:lastName", ns)) if p
                )
                if alias and alias != name:
                    aliases.append(alias)
        country = city = address = None
        countries: list[str] = []
        addresses: list[str] = []
        address_list = entry.find("ns:addressList", ns)
        if address_list is not None:
            for index, item in enumerate(address_list.findall("ns:address", ns)):
                a_country = _text(item, "ns:country", ns)
                a_city = _text(item, "ns:city", ns)
                text_parts = [
                    p
                    for p in (
                        _text(item, "ns:address1", ns),
                        _text(item, "ns:address2", ns),
                        a_city,
                        a_country,
                    )
                    if p
                ]
                joined = ", ".join(text_parts) if text_parts else None
                if index == 0:
                    country, city, address = a_country, a_city, joined
                if a_country and a_country not in countries:
                    countries.append(a_country)
                if joined:
                    addresses.append(joined)
        births = [
            (item.text or "").strip()
            for item in entry.findall("ns:dateOfBirthList/ns:dateOfBirthItem/ns:dateOfBirth", ns)
            if item.text and item.text.strip()
        ]
        records.append(
            {
                "list_id": uid,
                "entity_type": "individual" if sdn_type.lower() == "individual" else "entity",
                "name": name,
                "aliases": aliases or None,
                "vat_ids": buckets["vat"] or None,
                "tax_ids": buckets["tax"] or None,
                "registration_numbers": buckets["registration"] or None,
                "passport_numbers": buckets["passport"] or None,
                "country": country,
                "address": address,
                "city": city,
                "sanction_programs": programs or None,
                "sanction_reasons": _text(entry, "ns:remarks", ns),
                EXTRA: {
                    "birth_dates": births,
                    "countries": countries,
                    "addresses": addresses,
                    "schema_hint": sdn_type,
                },
            }
        )
    return records, skipped


def _un_person(item: Element, mode: DateMode) -> dict[str, Any] | None:
    name = " ".join(
        p
        for p in (_text(item, "FIRST_NAME"), _text(item, "SECOND_NAME"), _text(item, "THIRD_NAME"))
        if p
    )
    if not name:
        return None
    aliases = [
        a
        for a in (_text(x, "ALIAS_NAME") for x in item.findall("INDIVIDUAL_ALIAS"))
        if a and a != name
    ]
    nationality = None
    nationalities: list[str] = []
    nat = item.find("NATIONALITY")
    if nat is not None:
        nationality = _text(nat, "VALUE")
        nationalities = [v.text.strip() for v in nat.findall("VALUE") if v.text and v.text.strip()]
    birth: date | str | None = None
    births: list[str] = []
    for index, dob in enumerate(item.findall("INDIVIDUAL_DATE_OF_BIRTH")):
        raw = _text(dob, "DATE")
        if index == 0:
            birth = _date(raw, mode)
        text_value = raw or _text(dob, "YEAR")
        if text_value:
            births.append(text_value)
    pob = None
    pob_elem = item.find("INDIVIDUAL_PLACE_OF_BIRTH")
    if pob_elem is not None:
        pob = _text(pob_elem, "CITY")
    country = city = address = None
    addr = item.find("INDIVIDUAL_ADDRESS")
    if addr is not None:
        country, city = _text(addr, "COUNTRY"), _text(addr, "CITY")
        parts = [p for p in (_text(addr, "STREET"), city, country) if p]
        address = ", ".join(parts) if parts else None
    list_type = _text(item, "UN_LIST_TYPE")
    passports = []
    for doc in item.findall("INDIVIDUAL_DOCUMENT"):
        number = _text(doc, "NUMBER")
        if number and "passport" in (_text(doc, "TYPE_OF_DOCUMENT") or "").lower():
            passports.append(number)
    listed = _text(item, "LISTED_ON")
    countries = [c for c in [country, *nationalities] if c]
    return {
        "list_id": _text(item, "DATAID"),
        "entity_type": "individual",
        "name": name,
        "aliases": aliases or None,
        "nationality": nationality,
        "date_of_birth": birth,
        "place_of_birth": pob,
        "country": country or nationality,
        "address": address,
        "city": city,
        "passport_numbers": passports or None,
        "sanction_programs": [list_type] if list_type else None,
        "sanction_reasons": _text(item, "COMMENTS1"),
        "listing_date": _date(listed, mode),
        EXTRA: {
            "birth_dates": births,
            "countries": list(dict.fromkeys(countries)),
            "addresses": [address] if address else [],
            "schema_hint": "individual",
        },
    }


def _un_entity(item: Element, mode: DateMode) -> dict[str, Any] | None:
    name = _text(item, "FIRST_NAME") or ""
    if not name:
        return None
    aliases = [
        a for a in (_text(x, "ALIAS_NAME") for x in item.findall("ENTITY_ALIAS")) if a and a != name
    ]
    country = city = address = None
    addr = item.find("ENTITY_ADDRESS")
    if addr is not None:
        country, city = _text(addr, "COUNTRY"), _text(addr, "CITY")
        parts = [p for p in (_text(addr, "STREET"), city, country) if p]
        address = ", ".join(parts) if parts else None
    list_type = _text(item, "UN_LIST_TYPE")
    return {
        "list_id": _text(item, "DATAID"),
        "entity_type": "entity",
        "name": name,
        "aliases": aliases or None,
        "country": country,
        "address": address,
        "city": city,
        "sanction_programs": [list_type] if list_type else None,
        "sanction_reasons": _text(item, "COMMENTS1"),
        "listing_date": _date(_text(item, "LISTED_ON"), mode),
        EXTRA: {
            "birth_dates": [],
            "countries": [country] if country else [],
            "addresses": [address] if address else [],
            "schema_hint": "entity",
        },
    }


def _parse_un(data: bytes, mode: DateMode) -> tuple[list[dict[str, Any]], list[str]]:
    root = _fromstring(data)
    records: list[dict[str, Any]] = []
    skipped: list[str] = []
    for group, tag, parse in (
        ("INDIVIDUALS", "INDIVIDUAL", _un_person),
        ("ENTITIES", "ENTITY", _un_entity),
    ):
        container = root.find(group)
        if container is None:
            continue
        for item in container.findall(tag):
            record = parse(item, mode)
            if record is None:
                skipped.append(_text(item, "DATAID") or "")
            else:
                records.append(record)
    return records, skipped


def _eu_birth(elem: Element, mode: DateMode) -> tuple[date | str | None, str | None, str | None]:
    """Date and place of birth of one ``birthdate`` element and its text form."""
    value: date | str | None = None
    raw = elem.get("birthdate", "").strip()
    text: str | None = raw or None
    if raw:
        value = _date(raw, mode)
    else:
        year, month, day = elem.get("year"), elem.get("monthOfYear"), elem.get("dayOfMonth")
        if year:
            text = "-".join([year] + [p.zfill(2) for p in (month, day if month else None) if p])
            if mode == "legacy":
                try:
                    value = date(int(year), int(month) if month else 1, int(day) if day else 1)
                except (ValueError, TypeError):
                    value = None
            else:
                value = text
    place = [
        p for p in (elem.get("city", "").strip(), elem.get("countryIso2Code", "").strip()) if p
    ]
    return value, (", ".join(place) if place else None), text


def _parse_eu(data: bytes, mode: DateMode) -> tuple[list[dict[str, Any]], list[str]]:
    root = _fromstring(data)
    ns = detect_namespace(root) or EU_NAMESPACE
    records: list[dict[str, Any]] = []
    skipped: list[str] = []
    for elem in root.findall("ns:sanctionEntity", ns):
        logical_id = elem.get("logicalId")
        name = ""
        aliases: list[str] = []
        for alias in elem.findall("ns:nameAlias", ns):
            whole = alias.get("wholeName", "").strip()
            if not whole:
                whole = " ".join(
                    p
                    for p in (alias.get("firstName", "").strip(), alias.get("lastName", "").strip())
                    if p
                )
            if not whole:
                continue
            if not name:
                name = whole
            elif whole != name:
                aliases.append(whole)
        if not name:
            skipped.append(logical_id or "")
            continue
        entity_type = "entity"
        subject = elem.find("ns:subjectType", ns)
        if subject is not None and subject.get("classificationCode", "") == "P":
            entity_type = "individual"
        pairs = [
            (
                ident.get("identificationTypeCode", ""),
                ident.get("identificationTypeDescription", "").lower(),
                ident.get("number", "").strip(),
            )
            for ident in elem.findall("ns:identification", ns)
        ]
        buckets = _id_buckets(pairs)
        country = city = address = None
        countries: list[str] = []
        addresses: list[str] = []
        for index, addr in enumerate(elem.findall("ns:address", ns)):
            a_country = addr.get("countryIso2Code") or addr.get("country")
            a_city = addr.get("city", "").strip() or None
            parts = [
                p
                for p in (
                    addr.get("street", "").strip() or None,
                    addr.get("zipCode", "").strip() or None,
                    a_city,
                    a_country,
                )
                if p
            ]
            joined = ", ".join(parts) if parts else None
            if index == 0:
                country, city, address = a_country, a_city, joined
            if a_country and a_country not in countries:
                countries.append(a_country)
            if joined:
                addresses.append(joined)
        birth: date | str | None = None
        place = None
        births: list[str] = []
        for index, bd in enumerate(elem.findall("ns:birthdate", ns)):
            value, bd_place, bd_text = _eu_birth(bd, mode)
            if index == 0:
                birth, place = value, bd_place
            if bd_text:
                births.append(bd_text)
        programs: list[str] = []
        for reg in elem.findall("ns:regulation", ns):
            programme = reg.get("programme", "").strip()
            if programme and programme not in programs:
                programs.append(programme)
        nationality = None
        citizenship = elem.find("ns:citizenship", ns)
        if citizenship is not None:
            nationality = citizenship.get("countryIso2Code") or citizenship.get(
                "countryDescription"
            )
        all_countries = list(dict.fromkeys(c for c in [*countries, nationality] if c))
        records.append(
            {
                "list_id": logical_id,
                "entity_type": entity_type,
                "name": name,
                "aliases": aliases or None,
                "vat_ids": buckets["vat"] or None,
                "tax_ids": buckets["tax"] or None,
                "registration_numbers": buckets["registration"] or None,
                "passport_numbers": buckets["passport"] or None,
                "country": country,
                "address": address,
                "city": city,
                "date_of_birth": birth,
                "place_of_birth": place,
                "nationality": nationality,
                "sanction_programs": programs or None,
                EXTRA: {
                    "birth_dates": births,
                    "countries": all_countries,
                    "addresses": addresses,
                    "schema_hint": entity_type,
                },
            }
        )
    return records, skipped


_PARSERS: dict[str, Callable[[bytes, DateMode], tuple[list[dict[str, Any]], list[str]]]] = {
    "eu_fsf_xml": _parse_eu,
    "ofac_sdn_xml": _parse_ofac,
    "un_sc_xml": _parse_un,
}


def parse_xml_list(data: bytes, format: str, *, dates: DateMode = "text") -> list[dict[str, Any]]:
    """Parser dictionaries of the originals (key sets differ per list).

    Raises the XML ``ParseError`` of the parser for malformed input, like the
    originals; :func:`xml_entries` wraps it into :class:`FormatError`.
    """
    if format not in _PARSERS:
        raise FormatError(f"Unbekanntes XML-Listenformat '{format}'.")
    records, _ = _PARSERS[format](data, dates)
    return [{k: v for k, v in r.items() if k != EXTRA} for r in records]


def to_simple_row(parsed: dict[str, Any]) -> dict[str, str]:
    """Parser dictionary → OpenSanctions ``targets.simple.csv`` row (portal adapter)."""

    def join(*lists: Any) -> str:
        """Join optional lists with ``;``."""
        parts: list[str] = []
        for values in lists:
            if values:
                parts.extend(str(x).strip() for x in values if str(x).strip())
        return ";".join(parts)

    def iso(value: Any) -> str:
        """ISO text of a date, the text itself, or ``""``."""
        if isinstance(value, date):
            return value.isoformat()
        return value if isinstance(value, str) else ""

    return {
        "id": str(parsed.get("list_id") or "").strip(),
        "schema": {"individual": "Person", "entity": "Organization"}.get(
            parsed.get("entity_type") or "", ""
        ),
        "name": str(parsed.get("name") or "").strip(),
        "aliases": join(parsed.get("aliases")),
        "birth_date": iso(parsed.get("date_of_birth")),
        "countries": str(parsed.get("country") or "").strip(),
        "addresses": str(parsed.get("address") or "").strip(),
        "identifiers": join(
            parsed.get("vat_ids"),
            parsed.get("tax_ids"),
            parsed.get("registration_numbers"),
            parsed.get("passport_numbers"),
        ),
        "sanctions": "",
        "program_ids": join(parsed.get("sanction_programs")),
        "first_seen": iso(parsed.get("listing_date")),
        "last_seen": "",
    }


def serialize_xml_list(parsed: list[dict[str, Any]]) -> bytes:
    """Portal-compatible ``targets.simple.csv`` bytes of parser dictionaries."""
    return serialize_targets_simple_csv((to_simple_row(p) for p in parsed), columns=PORTAL_COLUMNS)


def xml_entries(data: bytes, *, format: str, list_key: str) -> ParsedList:
    """Library contract: list entries with all birth dates/countries, skipped names as issues."""
    if format not in _PARSERS:
        raise FormatError(f"Unbekanntes XML-Listenformat '{format}'.")
    try:
        records, skipped = _PARSERS[format](data, "text")
    except DependencyError:
        raise
    except Exception as exc:  # noqa: BLE001 - every parser failure is a format error
        raise FormatError(f"XML-Liste '{list_key}' nicht lesbar: {exc}") from exc
    entries: list[ListEntry] = []
    issues = [RowIssue(0, "Name fehlt", key or None) for key in skipped]
    for record in records:
        row = to_simple_row(record)
        extra = record[EXTRA]
        if not row["id"]:
            issues.append(RowIssue(0, "Kennung fehlt", None))
            continue
        entries.append(
            ListEntry(
                list_key=list_key,
                entry_id=row["id"],
                schema=row["schema"],
                name=row["name"],
                aliases=tuple(record.get("aliases") or ()),
                birth_date=";".join(extra["birth_dates"]),
                countries=";".join(extra["countries"]),
                addresses="; ".join(extra["addresses"]),
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
