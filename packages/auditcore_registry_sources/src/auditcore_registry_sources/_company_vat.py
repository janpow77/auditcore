"""EU VIES VAT check: request, prefix-independent answer parsing and the transport call."""

from __future__ import annotations

import re
from dataclasses import dataclass
from xml.etree.ElementTree import Element  # noqa: S405 - type only; parsing uses defusedxml

from auditcore_common.safe_xml import defused_fromstring
from auditcore_harvest import ParserError, Transport, TransportError, raise_for_status

from ._types import JsonObject
from .errors import DependencyError, QueryError

VIES_URL = "https://ec.europa.eu/taxation_customs/vies/services/checkVatService"
_VAT = re.compile(r"^([A-Z]{2})(.+)$")
_SOAP = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:urn="urn:ec.europa.eu:taxud:vies:services:checkVat:types">
    <soapenv:Body>
        <urn:checkVat>
            <urn:countryCode>{country}</urn:countryCode>
            <urn:vatNumber>{number}</urn:vatNumber>
        </urn:checkVat>
    </soapenv:Body>
</soapenv:Envelope>"""
UNDISCLOSED = "---"


def split_vat_id(vat_id: str) -> tuple[str, str, str]:
    """Normalised VAT id, country code and number; a wrong format is a :class:`QueryError`."""
    compact = vat_id.replace(" ", "").upper()
    match = _VAT.match(compact)
    if not match:
        raise QueryError("USt-IdNr. hat kein gültiges Format (Ländercode + Nummer).")
    return compact, match.group(1), match.group(2)


def vies_request(vat_id: str) -> tuple[str, bytes, dict[str, str]]:
    """URL, SOAP body and headers of a ``checkVat`` request (escaped values)."""
    _, country, number = split_vat_id(vat_id)
    from xml.sax.saxutils import escape  # noqa: S406 - escaping only, no parsing

    body = _SOAP.format(country=escape(country), number=escape(number))
    return VIES_URL, body.encode("utf-8"), {"Content-Type": "text/xml; charset=utf-8"}


@dataclass(frozen=True)
class VatCheck:
    """VIES answer; ``status`` is ``VALID``, ``INVALID`` or ``UNAVAILABLE``."""

    status: str
    vat_id: str
    country_code: str
    request_date: str | None = None
    name: str | None = None
    address: str | None = None
    name_disclosed: bool = False
    fault: str | None = None

    def to_dict(self) -> JsonObject:
        """JSON view."""
        return {
            "status": self.status,
            "vat_id": self.vat_id,
            "country_code": self.country_code,
            "request_date": self.request_date,
            "name": self.name,
            "address": self.address,
            "name_disclosed": self.name_disclosed,
            "fault": self.fault,
        }


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].rsplit(":", 1)[-1]


def parse_vies_response(vat_id: str, body: bytes) -> VatCheck:
    """Interpret a ``checkVat`` answer regardless of namespace prefixes."""
    compact, country, _ = split_vat_id(vat_id)
    fromstring = defused_fromstring(
        DependencyError, "Für VIES ist 'auditcore_registry_sources[xml]' zu installieren."
    )
    try:
        root: Element = fromstring(body)
    except Exception as exc:  # noqa: BLE001 - every parser failure is a parser error
        raise ParserError(f"VIES-Antwort nicht lesbar: {exc}") from exc
    values: dict[str, str] = {}
    for element in root.iter():
        name = _local(element.tag)
        if name in ("valid", "name", "address", "requestDate", "faultstring", "countryCode"):
            values.setdefault(name, (element.text or "").strip())
    if "faultstring" in values:
        return VatCheck("UNAVAILABLE", compact, country, fault=values["faultstring"] or "Fault")
    if "valid" not in values:
        raise ParserError("VIES-Antwort ohne Gültigkeitsangabe.")
    found_name = values.get("name") or None
    address = values.get("address") or None
    disclosed = bool(found_name and found_name != UNDISCLOSED)
    return VatCheck(
        status="VALID" if values["valid"].lower() == "true" else "INVALID",
        vat_id=compact,
        country_code=values.get("countryCode") or country,
        request_date=values.get("requestDate") or None,
        name=found_name if disclosed else None,
        address=address if address and address != UNDISCLOSED else None,
        name_disclosed=disclosed,
    )


def check_vat(transport: Transport, vat_id: str, *, timeout: float = 15.0) -> VatCheck:
    """One VIES request through the injected transport; failures become ``UNAVAILABLE``."""
    url, body, headers = vies_request(vat_id)
    compact, country, _ = split_vat_id(vat_id)
    try:
        response = transport.request("POST", url, headers=headers, data=body, timeout=timeout)
        if response.status >= 500:
            # VIES reports MS_UNAVAILABLE and similar as SOAP faults with HTTP 500.
            try:
                return parse_vies_response(vat_id, response.body)
            except ParserError:
                pass
        raise_for_status(response)
    except TransportError as exc:
        return VatCheck("UNAVAILABLE", compact, country, fault=str(exc))
    return parse_vies_response(vat_id, response.body)
