"""UN Security Council consolidated list parser (originals' dictionaries plus extras)."""

from __future__ import annotations

from datetime import date
from xml.etree.ElementTree import Element  # noqa: S405 - type only; parsing uses defusedxml

from ._xml_support import (
    DateMode,
    ParsedRecord,
    ParseOutcome,
    RecordExtra,
    XmlRecord,
    _date,
    _fromstring,
    _text,
    join_present,
)


def _un_aliases(item: Element, tag: str, name: str) -> list[str]:
    aliases = (_text(x, "ALIAS_NAME") for x in item.findall(tag))
    return [a for a in aliases if a and a != name]


def _un_address(item: Element, tag: str) -> tuple[str | None, str | None, str | None]:
    """Country, city and joined text of the first address element."""
    addr = item.find(tag)
    if addr is None:
        return None, None, None
    country, city = _text(addr, "COUNTRY"), _text(addr, "CITY")
    return country, city, join_present((_text(addr, "STREET"), city, country))


def _un_nationalities(item: Element) -> tuple[str | None, list[str]]:
    nat = item.find("NATIONALITY")
    if nat is None:
        return None, []
    values = [v.text.strip() for v in nat.findall("VALUE") if v.text and v.text.strip()]
    return _text(nat, "VALUE"), values


def _un_births(item: Element, mode: DateMode) -> tuple[date | str | None, list[str]]:
    birth: date | str | None = None
    births: list[str] = []
    for index, dob in enumerate(item.findall("INDIVIDUAL_DATE_OF_BIRTH")):
        raw = _text(dob, "DATE")
        if index == 0:
            birth = _date(raw, mode)
        text_value = raw or _text(dob, "YEAR")
        if text_value:
            births.append(text_value)
    return birth, births


def _un_place_of_birth(item: Element) -> str | None:
    pob_elem = item.find("INDIVIDUAL_PLACE_OF_BIRTH")
    return None if pob_elem is None else _text(pob_elem, "CITY")


def _un_passports(item: Element) -> list[str]:
    passports = []
    for doc in item.findall("INDIVIDUAL_DOCUMENT"):
        number = _text(doc, "NUMBER")
        if number and "passport" in (_text(doc, "TYPE_OF_DOCUMENT") or "").lower():
            passports.append(number)
    return passports


def _un_person(item: Element, mode: DateMode) -> ParsedRecord | None:
    name = " ".join(
        p
        for p in (_text(item, "FIRST_NAME"), _text(item, "SECOND_NAME"), _text(item, "THIRD_NAME"))
        if p
    )
    if not name:
        return None
    aliases = _un_aliases(item, "INDIVIDUAL_ALIAS", name)
    nationality, nationalities = _un_nationalities(item)
    birth, births = _un_births(item, mode)
    pob = _un_place_of_birth(item)
    country, city, address = _un_address(item, "INDIVIDUAL_ADDRESS")
    list_type = _text(item, "UN_LIST_TYPE")
    passports = _un_passports(item)
    listed = _text(item, "LISTED_ON")
    countries = [c for c in [country, *nationalities] if c]
    fields: XmlRecord = {
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
    }
    extra = RecordExtra(
        births, list(dict.fromkeys(countries)), [address] if address else [], "individual"
    )
    return ParsedRecord(fields, extra)


def _un_entity(item: Element, mode: DateMode) -> ParsedRecord | None:
    name = _text(item, "FIRST_NAME") or ""
    if not name:
        return None
    aliases = _un_aliases(item, "ENTITY_ALIAS", name)
    country, city, address = _un_address(item, "ENTITY_ADDRESS")
    list_type = _text(item, "UN_LIST_TYPE")
    fields: XmlRecord = {
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
    }
    extra = RecordExtra([], [country] if country else [], [address] if address else [], "entity")
    return ParsedRecord(fields, extra)


def parse_un(data: bytes, mode: DateMode) -> ParseOutcome:
    """UN Security Council consolidated list: individuals, then entities."""
    root = _fromstring(data)
    records: list[ParsedRecord] = []
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
