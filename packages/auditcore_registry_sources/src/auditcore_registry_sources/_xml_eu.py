"""EU financial sanctions file (FSF 1.1) parser (originals' dictionaries plus extras)."""

from __future__ import annotations

from datetime import date
from xml.etree.ElementTree import Element  # noqa: S405 - type only; parsing uses defusedxml

from ._xml_support import (
    EU_NAMESPACE,
    AddressSummary,
    DateMode,
    ParsedRecord,
    ParseOutcome,
    RecordExtra,
    XmlRecord,
    _date,
    _fromstring,
    _id_buckets,
    detect_namespace,
    join_present,
)


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


def _eu_names(elem: Element, ns: dict[str, str]) -> tuple[str, list[str]]:
    """First non-empty spelling as the name, every other differing spelling as alias."""
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
    return name, aliases


def _eu_entity_type(elem: Element, ns: dict[str, str]) -> str:
    subject = elem.find("ns:subjectType", ns)
    if subject is not None and subject.get("classificationCode", "") == "P":
        return "individual"
    return "entity"


def _eu_addresses(elem: Element, ns: dict[str, str]) -> AddressSummary:
    summary = AddressSummary()
    for index, addr in enumerate(elem.findall("ns:address", ns)):
        country = addr.get("countryIso2Code") or addr.get("country")
        city = addr.get("city", "").strip() or None
        joined = join_present(
            (
                addr.get("street", "").strip() or None,
                addr.get("zipCode", "").strip() or None,
                city,
                country,
            )
        )
        summary.add(index, country, city, joined)
    return summary


def _eu_births(
    elem: Element, ns: dict[str, str], mode: DateMode
) -> tuple[date | str | None, str | None, list[str]]:
    birth: date | str | None = None
    place = None
    births: list[str] = []
    for index, bd in enumerate(elem.findall("ns:birthdate", ns)):
        value, bd_place, bd_text = _eu_birth(bd, mode)
        if index == 0:
            birth, place = value, bd_place
        if bd_text:
            births.append(bd_text)
    return birth, place, births


def _eu_programs(elem: Element, ns: dict[str, str]) -> list[str]:
    programs: list[str] = []
    for reg in elem.findall("ns:regulation", ns):
        programme = reg.get("programme", "").strip()
        if programme and programme not in programs:
            programs.append(programme)
    return programs


def _eu_nationality(elem: Element, ns: dict[str, str]) -> str | None:
    citizenship = elem.find("ns:citizenship", ns)
    if citizenship is None:
        return None
    return citizenship.get("countryIso2Code") or citizenship.get("countryDescription")


def _eu_record(elem: Element, ns: dict[str, str], mode: DateMode) -> ParsedRecord | None:
    name, aliases = _eu_names(elem, ns)
    if not name:
        return None
    entity_type = _eu_entity_type(elem, ns)
    pairs = [
        (
            ident.get("identificationTypeCode", ""),
            ident.get("identificationTypeDescription", "").lower(),
            ident.get("number", "").strip(),
        )
        for ident in elem.findall("ns:identification", ns)
    ]
    buckets = _id_buckets(pairs)
    places = _eu_addresses(elem, ns)
    birth, place, births = _eu_births(elem, ns, mode)
    programs = _eu_programs(elem, ns)
    nationality = _eu_nationality(elem, ns)
    all_countries = list(dict.fromkeys(c for c in [*places.countries, nationality] if c))
    fields: XmlRecord = {
        "list_id": elem.get("logicalId"),
        "entity_type": entity_type,
        "name": name,
        "aliases": aliases or None,
        "vat_ids": buckets["vat"] or None,
        "tax_ids": buckets["tax"] or None,
        "registration_numbers": buckets["registration"] or None,
        "passport_numbers": buckets["passport"] or None,
        "country": places.country,
        "address": places.address,
        "city": places.city,
        "date_of_birth": birth,
        "place_of_birth": place,
        "nationality": nationality,
        "sanction_programs": programs or None,
    }
    extra = RecordExtra(births, all_countries, places.addresses, entity_type)
    return ParsedRecord(fields, extra)


def parse_eu(data: bytes, mode: DateMode) -> ParseOutcome:
    """EU financial sanctions file (FSF 1.1); the namespace defaults to the EU export one."""
    root = _fromstring(data)
    ns = detect_namespace(root) or EU_NAMESPACE
    records: list[ParsedRecord] = []
    skipped: list[str] = []
    for elem in root.findall("ns:sanctionEntity", ns):
        record = _eu_record(elem, ns, mode)
        if record is None:
            skipped.append(elem.get("logicalId") or "")
        else:
            records.append(record)
    return records, skipped
