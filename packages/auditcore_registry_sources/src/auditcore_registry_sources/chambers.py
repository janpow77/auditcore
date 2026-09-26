"""Register and chamber address sources of the OSINT map (``traeger_quellen.py``).

* Zuwendungsempfängerregister of the BZSt (§ 60b AO): full JSON dump plus a
  status endpoint with the total count.
* The 79 chambers of industry and commerce (open JSON of the DIHK app service).
* The chambers of crafts from the ZDH address page (HTML text pattern; extra
  ``html`` for BeautifulSoup, as the source).

The parsers reproduce the source's reduction to name and address. Deliberate
difference: the source only prints the register's total and a warning when
fewer than 53 chambers of crafts were found; here both become issues that make
a delivery incomplete instead of a silent success.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, TypedDict

from auditcore_common.json_values import decode_json

from .errors import DependencyError, FormatError

ZER_REGISTER_URL = "https://zer.bzst.de/api/v1/register"
ZER_STATUS_URL = "https://zer.bzst.de/api/v1/status"
IHK_URL = "https://apps.ihk.de/app-service/rest/service/locations"
ZDH_URL = (
    "https://www.zdh.de/ueber-uns/organisationen-des-handwerks/"
    "handwerkskammern/adressen-der-handwerkskammern/"
)
#: Number of chambers of crafts the source expects on the ZDH page.
EXPECTED_HWK = 53

_PLZ = re.compile(r"^(\d{4,5})\s+(\D.*)$")
_STREET = re.compile(r"^(.+?)\s+(\d+[a-zA-Z]?(?:\s*[-–/]\s*\d+[a-zA-Z]?)?)$")


class ChamberRecord(TypedDict, total=False):
    """An address record; the register has ``land``, the chambers ``lat``/``lon``/``art``."""

    name: str
    plz: str
    ort: str
    strasse: str
    hnr: str
    land: str
    lat: float | None
    lon: float | None
    art: str


@dataclass(frozen=True)
class AddressDelivery:
    """Parsed address records with the rows the source drops and open issues."""

    records: tuple[ChamberRecord, ...]
    rows_seen: int
    dropped: int
    issues: tuple[str, ...]
    reported_total: int | None = None

    @property
    def complete(self) -> bool:
        """No issue (for example a count that differs from the reported total)."""
        return not self.issues


def _json(data: bytes, what: str) -> Any:
    return decode_json(
        data, lambda exc: FormatError(f"{what}: keine gültige JSON-Antwort ({exc}).")
    )


def parse_zer_status(data: bytes) -> int:
    """Total number of entries reported by the register's status endpoint."""
    status = _json(data, "ZER-Status")
    try:
        return int(status["total"])
    except (KeyError, TypeError, ValueError) as exc:
        raise FormatError("ZER-Status ohne Gesamtzahl.") from exc


def parse_zer_register(data: bytes, *, reported_total: int | None = None) -> AddressDelivery:
    """Full dump → name, postcode, place, street, house number, federal state.

    Rows without name or postcode are dropped as in the source; a difference
    between the rows delivered and the reported total is an issue.
    """
    rows = _json(data, "ZER-Register")
    if not isinstance(rows, list):
        raise FormatError("ZER-Register: erwartet wird eine Liste.")
    records: list[ChamberRecord] = []
    for row in rows:
        name = (row.get("label") or "").strip()
        plz = (row.get("plz") or "").strip()
        if not name or not plz:
            continue
        records.append(
            {
                "name": name,
                "plz": plz,
                "ort": (row.get("ort") or "").strip(),
                "strasse": (row.get("strasse") or "").strip(),
                "hnr": (row.get("hausnummer") or "").strip(),
                "land": (row.get("bundesland") or "").strip(),
            }
        )
    issues = []
    if reported_total is not None and reported_total != len(rows):
        issues.append(
            f"Das Register meldet {reported_total} Einträge, geliefert wurden {len(rows)}."
        )
    if not rows:
        raise FormatError("ZER-Register: leere Lieferung.")
    return AddressDelivery(
        tuple(records), len(rows), len(rows) - len(records), tuple(issues), reported_total
    )


def parse_ihk_locations(data: bytes) -> AddressDelivery:
    """Chambers of industry and commerce with coordinates (list or ``{"locations": [...]}``)."""
    raw = _json(data, "IHK-Standorte")
    entries = raw if isinstance(raw, list) else raw.get("locations", raw)
    if not isinstance(entries, list):
        raise FormatError("IHK-Standorte: erwartet wird eine Liste.")
    chambers: list[ChamberRecord] = []
    for item in entries:
        geo = item.get("geodata") or []
        chambers.append(
            {
                "name": (item.get("name") or "").strip(),
                "strasse": (item.get("street") or "").strip(),
                "plz": (item.get("zip") or "").strip(),
                "ort": (item.get("city") or "").strip(),
                "lat": float(geo[0]) if len(geo) == 2 else None,
                "lon": float(geo[1]) if len(geo) == 2 else None,
                "art": "IHK",
            }
        )
    kept = [c for c in chambers if c["name"]]
    return AddressDelivery(tuple(kept), len(entries), len(entries) - len(kept), ())


def page_lines(html: bytes) -> list[str]:
    """Non-empty text lines of a page, as BeautifulSoup ``get_text("\\n")`` yields them."""
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:  # pragma: no cover - exercised in the installed smoke test
        raise DependencyError(
            "Für die Handwerkskammerseite ist 'auditcore_registry_sources[html]' zu installieren."
        ) from exc
    text = BeautifulSoup(html, "html.parser").get_text("\n")
    return [line.strip() for line in text.split("\n") if line.strip()]


def parse_hwk_page(html: bytes, *, expected: int | None = EXPECTED_HWK) -> AddressDelivery:
    """Chambers of crafts from the pattern ``Name / Straße Nr. / PLZ Ort``.

    Four-digit postcodes are accepted and padded (the page drops the leading
    zero, e.g. Chemnitz ``9116``); post office boxes are skipped. Fewer
    chambers than ``expected`` is an issue (the page has probably changed).
    """
    lines = page_lines(html)
    chambers: list[ChamberRecord] = []
    for index, line in enumerate(lines):
        found = _PLZ.match(line)
        if not found or index < 2:
            continue
        street_line, name_line = lines[index - 1], lines[index - 2]
        if street_line.lower().startswith("postfach"):
            continue
        street = _STREET.match(street_line)
        if not street or "handwerkskammer" not in name_line.lower():
            continue
        chambers.append(
            {
                "name": name_line.strip(),
                "strasse": street.group(1).strip(),
                "hnr": street.group(2).strip(),
                "plz": found.group(1).zfill(5),
                "ort": found.group(2).strip(),
                "lat": None,
                "lon": None,
                "art": "HWK",
            }
        )
    issues = []
    if expected is not None and len(chambers) < expected:
        issues.append(
            f"Nur {len(chambers)} statt {expected} Handwerkskammern erkannt; die Seite hat sich "
            "vermutlich geändert."
        )
    return AddressDelivery(tuple(chambers), len(lines), 0, tuple(issues))
