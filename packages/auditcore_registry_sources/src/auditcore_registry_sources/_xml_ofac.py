"""OFAC SDN XML parser (dictionaries of the originals plus :class:`RecordExtra`)."""

from __future__ import annotations

from xml.etree.ElementTree import Element  # noqa: S405 - type only; parsing uses defusedxml

from ._xml_support import (
    AddressSummary,
    DateMode,
    ParsedRecord,
    ParseOutcome,
    RecordExtra,
    XmlRecord,
    _fromstring,
    _id_buckets,
    _text,
    detect_namespace,
    join_present,
)


def _ofac_name(element: Element, ns: dict[str, str]) -> str:
    return " ".join(
        p for p in (_text(element, "ns:firstName", ns), _text(element, "ns:lastName", ns)) if p
    )


def _ofac_programs(entry: Element, ns: dict[str, str]) -> list[str]:
    program_list = entry.find("ns:programList", ns)
    if program_list is None:
        return []
    return [
        p.text.strip() for p in program_list.findall("ns:program", ns) if p.text and p.text.strip()
    ]


def _ofac_id_pairs(entry: Element, ns: dict[str, str]) -> list[tuple[str, str, str]]:
    id_list = entry.find("ns:idList", ns)
    if id_list is None:
        return []
    # The source never matches "passport" by code; only the type text counts.
    return [
        ("", (_text(item, "ns:idType", ns) or "").lower(), _text(item, "ns:idNumber", ns) or "")
        for item in id_list.findall("ns:id", ns)
    ]


def _ofac_aliases(entry: Element, ns: dict[str, str], name: str) -> list[str]:
    aka_list = entry.find("ns:akaList", ns)
    if aka_list is None:
        return []
    aliases = (_ofac_name(aka, ns) for aka in aka_list.findall("ns:aka", ns))
    return [alias for alias in aliases if alias and alias != name]


def _ofac_addresses(entry: Element, ns: dict[str, str]) -> AddressSummary:
    summary = AddressSummary()
    address_list = entry.find("ns:addressList", ns)
    if address_list is None:
        return summary
    for index, item in enumerate(address_list.findall("ns:address", ns)):
        country = _text(item, "ns:country", ns)
        city = _text(item, "ns:city", ns)
        joined = join_present(
            (_text(item, "ns:address1", ns), _text(item, "ns:address2", ns), city, country)
        )
        summary.add(index, country, city, joined)
    return summary


def _ofac_record(entry: Element, ns: dict[str, str], name: str) -> ParsedRecord:
    sdn_type = _text(entry, "ns:sdnType", ns) or ""
    buckets = _id_buckets(_ofac_id_pairs(entry, ns))
    aliases = _ofac_aliases(entry, ns, name)
    places = _ofac_addresses(entry, ns)
    births = [
        (item.text or "").strip()
        for item in entry.findall("ns:dateOfBirthList/ns:dateOfBirthItem/ns:dateOfBirth", ns)
        if item.text and item.text.strip()
    ]
    programs = _ofac_programs(entry, ns)
    fields: XmlRecord = {
        "list_id": _text(entry, "ns:uid", ns),
        "entity_type": "individual" if sdn_type.lower() == "individual" else "entity",
        "name": name,
        "aliases": aliases or None,
        "vat_ids": buckets["vat"] or None,
        "tax_ids": buckets["tax"] or None,
        "registration_numbers": buckets["registration"] or None,
        "passport_numbers": buckets["passport"] or None,
        "country": places.country,
        "address": places.address,
        "city": places.city,
        "sanction_programs": programs or None,
        "sanction_reasons": _text(entry, "ns:remarks", ns),
    }
    extra = RecordExtra(births, places.countries, places.addresses, sdn_type)
    return ParsedRecord(fields, extra)


def parse_ofac(data: bytes, mode: DateMode) -> ParseOutcome:
    """OFAC SDN XML (``mode`` is irrelevant: the originals read no dates here)."""
    root = _fromstring(data)
    ns = detect_namespace(root)
    records: list[ParsedRecord] = []
    skipped: list[str] = []
    for entry in root.findall("ns:sdnEntry", ns):
        name = _ofac_name(entry, ns)
        if not name:
            skipped.append(_text(entry, "ns:uid", ns) or "")
            continue
        records.append(_ofac_record(entry, ns, name))
    return records, skipped
