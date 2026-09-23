"""Bundestag DIP (Dokumentations- und Informationssystem) request and response contract.

Pure functions: build query parameters, parse one response page with its
cursor and normalize ``drucksache`` items. Fetching, retries, paging order and
checkpoints are done by the ``auditcore_harvest`` engine through the adapter.

The API key is sent as ``Authorization: ApiKey …`` header supplied by the
consumer's credential provider; it never appears in URLs, parameters,
provenance or logs (source applications put a hard-coded key into the query).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

from .errors import ConfigurationError, ParseError
from .model import LegalDocument
from .normalize import parse_publication_date
from .profile import SourceProfile

SOURCE_ID = "dip_bundestag"
AUTH_HEADER = "Authorization"
DRUCKSACHE_PATH = "/drucksache"


def auth_header_value(api_key: str) -> str:
    """Header value for the DIP API key; rejects empty or multi-line keys."""
    if not isinstance(api_key, str) or not api_key.strip() or any(c in api_key for c in "\r\n"):
        raise ConfigurationError("DIP-API-Schlüssel fehlt oder ist ungültig.")
    return f"ApiKey {api_key.strip()}"


def drucksache_query(
    profile: SourceProfile,
    keyword: str,
    *,
    cursor: str | None = None,
    updated_since: date | None = None,
) -> dict[str, str]:
    """Query parameters for one ``/drucksache`` title search page (no credentials)."""
    if not isinstance(keyword, str) or not keyword.strip():
        raise ConfigurationError("DIP-Suchbegriff fehlt.")
    params = {"format": "json", "num": str(profile.dip_page_size), "f.titel": keyword}
    if cursor:
        params["cursor"] = cursor
    if updated_since is not None:
        params["f.aktualisiert.start"] = updated_since.isoformat()
    return params


def drucksache_url(profile: SourceProfile) -> str:
    """Absolute endpoint URL of the ``drucksache`` search."""
    return profile.dip_api_url.rstrip("/") + DRUCKSACHE_PATH


@dataclass(frozen=True)
class DipPage:
    """One parsed response page."""

    items: tuple[Mapping[str, Any], ...]
    cursor: str | None
    num_found: int | None

    def is_last(self, previous_cursor: str | None) -> bool:
        """DIP signals the end when the cursor no longer changes or no items arrive."""
        return not self.items or self.cursor is None or self.cursor == previous_cursor


def parse_page(payload: Any) -> DipPage:
    """Validate the documented ``{"numFound", "cursor", "documents"}`` shape.

    Raises:
        ParseError: missing or malformed ``documents``; never an empty success.
    """
    if not isinstance(payload, Mapping):
        raise ParseError("DIP-Antwort ist kein JSON-Objekt.", source_id=SOURCE_ID)
    documents = payload.get("documents")
    if not isinstance(documents, list) or not all(isinstance(d, Mapping) for d in documents):
        raise ParseError(
            "DIP-Antwort enthält keine Dokumentliste.", source_id=SOURCE_ID, location="documents"
        )
    cursor = payload.get("cursor")
    found = payload.get("numFound")
    return DipPage(
        items=tuple(documents),
        cursor=str(cursor) if cursor is not None else None,
        num_found=found if isinstance(found, int) and not isinstance(found, bool) else None,
    )


def _pdf_url(item: Mapping[str, Any], number: str) -> str | None:
    fundstelle = item.get("fundstelle")
    if isinstance(fundstelle, Mapping) and isinstance(fundstelle.get("pdf_url"), str):
        return str(fundstelle["pdf_url"])
    try:
        period, serial = number.split("/")
    except ValueError:
        return None
    if not (period.isdigit() and serial.isdigit()):
        return None
    padded = serial.zfill(5)
    return f"https://dserver.bundestag.de/btd/{period}/{padded[:3]}/{period}{padded}.pdf"


def _classification(profile: SourceProfile, title: str, raw_date: str) -> dict[str, Any]:
    if profile.dip_classification != "auditdatabase.dip":
        return {}
    period = "2021-2027"
    if raw_date[:4].isdigit() and int(raw_date[:4]) < 2021:
        period = "2014-2020"
    lower = title.lower()
    fund = (
        "ESF+"
        if ("esf" in lower or "sozialfonds" in lower)
        else ("Interreg" if "interreg" in lower else "EFRE")
    )
    return {"funding_period": period, "fund": fund, "rule": "auditdatabase.dip", "heuristic": True}


def normalize_drucksache(item: Mapping[str, Any], profile: SourceProfile) -> LegalDocument:
    """Normalize one ``drucksache`` item.

    Raises:
        ParseError: item without ``id`` or ``titel`` (the sources substituted
            ``""``/``"Ohne Titel"`` and stored documents without identity).
    """
    identifier = item.get("id")
    title = item.get("titel")
    if (
        not isinstance(identifier, (str, int))
        or isinstance(identifier, bool)
        or not str(identifier)
    ):
        raise ParseError("DIP-Drucksache ohne ID.", source_id=SOURCE_ID, location="id")
    if not isinstance(title, str) or not title.strip():
        raise ParseError(
            f"DIP-Drucksache {identifier} ohne Titel.", source_id=SOURCE_ID, location="titel"
        )
    number = str(item.get("dokumentnummer") or item.get("drucksacheNummer") or "")
    raw_date = str(item.get("datum") or "")
    published, precision = parse_publication_date(raw_date)
    abstract = item.get("abstract") if isinstance(item.get("abstract"), str) else ""
    portal = profile.dip_portal_url.rstrip("/")
    return LegalDocument(
        source_id=SOURCE_ID,
        external_id=f"dip_{identifier}",
        title=title,
        publication_date=published,
        date_precision=precision,
        raw_date=raw_date or None,
        source_url=f"{portal}/drucksache/{number}" if number else f"{portal}/{identifier}",
        document_url=_pdf_url(item, number) if number or item.get("fundstelle") else None,
        document_type=str(item.get("drucksachetyp") or "Drucksache"),
        language="de",
        content=abstract or title,
        abstract=abstract or None,
        classification=_classification(profile, title, raw_date),
        metadata={
            "drucksache_nummer": number,
            "wahlperiode": item.get("wahlperiode"),
            "urheber": list(item.get("urheber") or []),
            "autoren": item.get("autoren_anzeige", ""),
            "vorgangsbezug": list(item.get("vorgangsbezug") or []),
        },
        profile=profile.reference,
        adapter="dip.drucksache",
    )


def normalize_page(
    page: DipPage, profile: SourceProfile
) -> tuple[list[LegalDocument], list[ParseError]]:
    """Normalize all items; defective items are reported, not silently dropped."""
    documents: list[LegalDocument] = []
    errors: list[ParseError] = []
    for index, item in enumerate(page.items):
        try:
            documents.append(normalize_drucksache(item, profile))
        except ParseError as exc:
            exc.location = f"documents[{index}].{exc.location}"
            errors.append(exc)
    return documents, errors


def keywords(profile: SourceProfile, selected: Sequence[str] | None = None) -> tuple[str, ...]:
    """Profile search terms, optionally restricted to an explicit subset of them."""
    if selected is None:
        return profile.dip_keywords
    unknown = sorted(set(selected) - set(profile.dip_keywords))
    if unknown:
        raise ConfigurationError(f"Suchbegriffe nicht im Profil: {', '.join(unknown)}.")
    return tuple(selected)
