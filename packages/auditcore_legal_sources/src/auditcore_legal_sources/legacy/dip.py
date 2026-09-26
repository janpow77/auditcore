"""Legacy DIP flows: auditdatabase ``DIPHarvester`` and audit_designer ``BundestagDIPHarvester``."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence

from auditcore_harvest import JSON


def _legacy_pdf_url(doc: Mapping[str, JSON], number: object, period_number: object) -> object:
    """``fundstelle.pdf_url``, else the dserver URL derived from ``WP/NR``."""
    pdf_url = None
    fundstelle = doc.get("fundstelle", {})
    if isinstance(fundstelle, dict):
        pdf_url = fundstelle.get("pdf_url")
    if not pdf_url and number and period_number:
        try:
            wp, nr = str(number).split("/")
            padded = nr.zfill(5)
            pdf_url = f"https://dserver.bundestag.de/btd/{wp}/{padded[:3]}/{wp}{padded}.pdf"
        except Exception:  # noqa: BLE001 - reproduces the bare except of the source
            pass
    return pdf_url


def _legacy_funding_period(datum: JSON) -> str:
    """2021-2027 unless the date starts with a year before 2021."""
    if datum:
        try:
            if int(datum[:4]) < 2021:
                return "2014-2020"
        except Exception:  # noqa: BLE001 - reproduces the bare except of the source
            pass
    return "2021-2027"


def _legacy_fund(title: JSON) -> str:
    """Title keyword rule; EFRE when nothing matches."""
    lower = title.lower()
    if "esf" in lower or "sozialfonds" in lower:
        return "ESF+"
    if "interreg" in lower:
        return "Interreg"
    return "EFRE"


def legacy_dip_normalize(doc: Mapping[str, JSON]) -> dict[str, JSON] | None:
    """auditdatabase ``DIPHarvester._normalize_drucksache``."""
    try:
        doc_id = doc.get("id", "")
        title = doc.get("titel", "Ohne Titel")
        number = doc.get("dokumentnummer", doc.get("drucksacheNummer", ""))
        period_number = doc.get("wahlperiode", "")
        datum = doc.get("datum", "")
        pdf_url = _legacy_pdf_url(doc, number, period_number)
        funding_period = _legacy_funding_period(datum)
        fund = _legacy_fund(title)
        return {
            "id": f"dip_{doc_id}",
            "title": title,
            "document_type": doc.get("drucksachetyp", "Drucksache"),
            "source": "dip_bundestag",
            "source_url": f"https://dip.bundestag.de/drucksache/{number}"
            if number
            else f"https://dip.bundestag.de/{doc_id}",
            "pdf_url": pdf_url,
            "funding_period": funding_period,
            "fund": fund,
            "published_date": datum,
            "metadata": {
                "drucksache_nummer": number,
                "wahlperiode": period_number,
                "urheber": doc.get("urheber", []),
                "autoren": doc.get("autoren_anzeige", ""),
                "vorgangsbezug": doc.get("vorgangsbezug", []),
                "abstract": doc.get("abstract", ""),
            },
            "content": doc.get("abstract", "") or title,
        }
    except Exception:  # noqa: BLE001 - source returned None for any normalization error
        return None


def legacy_dip_query(api_key: str, keyword: str, limit: int = 30) -> dict[str, JSON]:
    """Query parameters the source sent per keyword (API key in the query string)."""
    return {"apikey": api_key, "format": "json", "num": min(limit, 100), "f.titel": keyword}


async def legacy_dip_harvest(
    fetch: Callable[[str, dict[str, JSON]], Awaitable[tuple[int, JSON]]],
    keywords: Sequence[str],
    api_key: str,
    limit: int = 200,
) -> dict[str, JSON]:
    """``DIPHarvester.harvest`` flow: every keyword, dedupe by id, truncate, errors swallowed.

    ``fetch(url, params)`` returns ``(status_code, parsed_json)`` or raises. As
    in the source, failures of single keywords only drop their results and the
    result is ``success=True`` even when every request failed.
    """
    documents: list[dict[str, JSON]] = []
    url = "https://search.dip.bundestag.de/api/v1/drucksache"
    for keyword in keywords:
        try:
            status, data = await fetch(url, legacy_dip_query(api_key, keyword, 30))
            if status == 200:
                for doc in data.get("documents", []):
                    normalized = legacy_dip_normalize(doc)
                    if normalized:
                        documents.append(normalized)
        except Exception:  # noqa: BLE001 - reproduces the swallowed per-keyword error
            continue
    seen: set[str] = set()
    unique = []
    for doc in documents:
        if doc["id"] not in seen:
            seen.add(doc["id"])
            unique.append(doc)
    return {
        "source_id": "dip_bundestag",
        "method_used": "REST_API",
        "documents": unique[:limit],
        "success": True,
        "error": None,
        "fallback_used": False,
    }


def designer_dip_drucksache(item: Mapping[str, JSON], query: str) -> dict[str, JSON] | None:
    """audit_designer ``BundestagDIPHarvester._parse_drucksache``."""
    title = item.get("titel", item.get("title", ""))
    number = item.get("dokumentnummer", item.get("drucksachenummer", ""))
    if not title:
        return None
    datum = item.get("datum", "")
    if datum:
        datum = datum[:10]
    return {
        "external_id": f"dip_ds_{number or item.get('id', '')}",
        "title": title,
        "source_url": f"https://dip.bundestag.de/drucksache/{number}" if number else "",
        "publication_date": datum,
        "document_type": item.get("drucksachetyp", "Drucksache"),
        "language": "de",
        "metadata": {
            "dokumentnummer": number,
            "wahlperiode": item.get("wahlperiode"),
            "drucksachetyp": item.get("drucksachetyp"),
            "herausgeber": item.get("herausgeber"),
            "urheber": item.get("urheber", []),
            "query": query,
            "api_id": item.get("id"),
        },
    }


def designer_dip_vorgang(item: Mapping[str, JSON], query: str) -> dict[str, JSON] | None:
    """audit_designer ``BundestagDIPHarvester._parse_vorgang``."""
    title = item.get("titel", item.get("title", ""))
    identifier = item.get("id", "")
    if not title:
        return None
    datum = item.get("datum", item.get("aktualisiert", ""))
    if datum:
        datum = datum[:10]
    return {
        "external_id": f"dip_vg_{identifier}",
        "title": title,
        "source_url": f"https://dip.bundestag.de/vorgang/{identifier}" if identifier else "",
        "publication_date": datum,
        "document_type": item.get("vorgangstyp", "Vorgang"),
        "language": "de",
        "metadata": {
            "vorgang_id": identifier,
            "wahlperiode": item.get("wahlperiode"),
            "vorgangstyp": item.get("vorgangstyp"),
            "initiative": item.get("initiative"),
            "beratungsstand": item.get("beratungsstand"),
            "query": query,
        },
    }
