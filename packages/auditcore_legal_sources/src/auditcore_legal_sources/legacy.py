"""Behavior-compatible adapters of the two characterized source applications.

``auditdatabase@bba911e`` (``app/harvester``) and ``audit_designer@030a71e``
(``app/modules/vp_ai/harvester``) are reproduced exactly, including defects
this package corrects in its own contract (``docs/behavior-changes.md``):
no string date is ever parsed, all-failing DIP searches report success and
the DIP document dictionary uses keys the ingestion service does not read.

The functions exist so consumers can switch to the installed package without
changing stored results and so every difference stays testable.
"""

from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from datetime import datetime
from typing import Any

from .eurlex import celex_document_type
from .normalize import detect_fund, funding_period_auditdatabase, funding_period_designer
from .profile import SourceProfile

_LEGACY_FORMATS = ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d.%m.%Y", "%Y")


def legacy_parse_date(value: Any) -> datetime | None:
    """``BaseHarvester._parse_date`` of both applications, slicing defect included."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        for fmt in _LEGACY_FORMATS:
            try:
                return datetime.strptime(value[: len(fmt.replace("%", ""))], fmt)
            except ValueError:
                continue
    return None


def legacy_detect_funding_period(text: str | None) -> str | None:
    """auditdatabase ``_detect_funding_period``."""
    return funding_period_auditdatabase(text)


def designer_detect_funding_period(
    text: str | None, publication_date: str | None = None
) -> str | None:
    """audit_designer ``detect_funding_period`` (text rules, then year)."""
    return funding_period_designer(text, publication_date)


def legacy_detect_fund(text: str | None) -> str | None:
    """``_detect_fund`` (identical in both applications)."""
    return detect_fund(text)


def legacy_is_relevant(text: str | None, keywords: Iterable[str]) -> bool:
    """``is_relevant`` without database keywords."""
    if not text:
        return False
    lower = text.lower()
    return any(keyword.lower() in lower for keyword in keywords)


def legacy_content_hash(content: str | None, abstract: str | None, title: str) -> str:
    """``HarvestedDocument.content_hash``."""
    text = content or abstract or title
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def legacy_harvested_document(source_id: str, **fields: Any) -> dict[str, Any]:
    """``vars(HarvestedDocument(...))`` of auditdatabase with its defaults."""
    return {
        "source_id": source_id,
        "external_id": fields["external_id"],
        "title": fields["title"],
        "content": fields.get("content"),
        "abstract": fields.get("abstract"),
        "publication_date": fields.get("publication_date"),
        "source_url": fields.get("source_url"),
        "document_type": fields.get("document_type"),
        "language": fields.get("language", "de"),
        "funding_period": fields.get("funding_period"),
        "fund": fields.get("fund"),
        "metadata": fields.get("metadata", {}),
    }


def legacy_normalize_document(source_id: str, raw: Mapping[str, Any]) -> dict[str, Any]:
    """auditdatabase ``BaseHarvester.normalize_document``."""
    return legacy_harvested_document(
        source_id,
        external_id=raw.get("external_id", raw.get("id", "")),
        title=raw.get("title", ""),
        content=raw.get("content"),
        abstract=raw.get("abstract", raw.get("summary")),
        publication_date=legacy_parse_date(raw.get("publication_date", raw.get("date"))),
        source_url=raw.get("source_url", raw.get("url", raw.get("link"))),
        document_type=raw.get("document_type", raw.get("type")),
        language=raw.get("language", "de"),
        funding_period=raw.get("funding_period"),
        fund=raw.get("fund"),
        metadata=raw.get("metadata", {}),
    )


# ---------------------------------------------------------------------------
# DIP (auditdatabase)
# ---------------------------------------------------------------------------


def legacy_dip_normalize(doc: Mapping[str, Any]) -> dict[str, Any] | None:
    """auditdatabase ``DIPHarvester._normalize_drucksache``."""
    try:
        doc_id = doc.get("id", "")
        title = doc.get("titel", "Ohne Titel")
        number = doc.get("dokumentnummer", doc.get("drucksacheNummer", ""))
        period_number = doc.get("wahlperiode", "")
        datum = doc.get("datum", "")
        kind = doc.get("drucksachetyp", "Drucksache")
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
        funding_period = "2021-2027"
        if datum:
            try:
                if int(datum[:4]) < 2021:
                    funding_period = "2014-2020"
            except Exception:  # noqa: BLE001
                pass
        lower = title.lower()
        if "esf" in lower or "sozialfonds" in lower:
            fund = "ESF+"
        elif "interreg" in lower:
            fund = "Interreg"
        else:
            fund = "EFRE"
        return {
            "id": f"dip_{doc_id}",
            "title": title,
            "document_type": kind,
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


def legacy_dip_query(api_key: str, keyword: str, limit: int = 30) -> dict[str, Any]:
    """Query parameters the source sent per keyword (API key in the query string)."""
    return {"apikey": api_key, "format": "json", "num": min(limit, 100), "f.titel": keyword}


async def legacy_dip_harvest(
    fetch: Callable[[str, dict[str, Any]], Awaitable[tuple[int, Any]]],
    keywords: Sequence[str],
    api_key: str,
    limit: int = 200,
) -> dict[str, Any]:
    """``DIPHarvester.harvest`` flow: every keyword, dedupe by id, truncate, errors swallowed.

    ``fetch(url, params)`` returns ``(status_code, parsed_json)`` or raises. As
    in the source, failures of single keywords only drop their results and the
    result is ``success=True`` even when every request failed.
    """
    documents: list[dict[str, Any]] = []
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


# ---------------------------------------------------------------------------
# EUR-Lex (auditdatabase and designer)
# ---------------------------------------------------------------------------


def legacy_celex_type(celex: str) -> str:
    """``_detect_document_type`` (identical in both applications)."""
    return celex_document_type(celex)


def legacy_eurlex_normalize(raw: Mapping[str, Any], *, designer: bool = False) -> dict[str, Any]:
    """``_normalize_eurlex_doc`` as ``vars(HarvestedDocument)`` of the respective application."""
    celex = raw.get("celex", "")
    title = raw.get("title", "")
    period = raw.get("funding_period")
    if not period:
        text = celex + " " + title
        period = (
            designer_detect_funding_period(text) if designer else legacy_detect_funding_period(text)
        )
    document = legacy_harvested_document(
        "eurlex",
        external_id=celex,
        title=title,
        publication_date=legacy_parse_date(raw.get("date", "")),
        source_url=f"https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:{celex}",
        document_type=legacy_celex_type(celex),
        language="de",
        funding_period=period,
        fund=legacy_detect_fund(title),
        metadata={"celex": celex, "query_source": raw.get("source"), "raw_type": raw.get("type")},
    )
    if designer:
        ordered = {}
        for key, value in document.items():
            ordered[key] = value
            if key == "publication_date":
                ordered["date_precision"] = "day"
            if key == "fund":
                ordered["kategorie"] = None
        return ordered
    return document


def legacy_sparql_rows(results: Mapping[str, Any]) -> list[dict[str, str]]:
    """``_execute_sparql`` result flattening (missing structures become empty)."""
    rows = []
    for binding in results.get("results", {}).get("bindings", []):
        rows.append({var: value.get("value", "") for var, value in binding.items()})
    return rows


async def legacy_eurlex_harvest(
    profile: SourceProfile,
    execute: Callable[[str], Awaitable[list[dict[str, str]]]],
    *,
    designer: bool = False,
) -> dict[str, Any]:
    """``EURLexHarvester.harvest``: core documents, queries, failed queries skipped silently."""
    documents: list[dict[str, Any]] = []
    seen: set[str] = set()
    for core in profile.eurlex_core_documents:
        if core.celex not in seen:
            documents.append(
                {
                    "celex": core.celex,
                    "title": core.title,
                    "funding_period": core.period,
                    "source": "core_documents",
                }
            )
            seen.add(core.celex)
    for name, query in profile.eurlex_queries.items():
        try:
            results = await execute(query)
        except Exception:  # noqa: BLE001 - reproduces the swallowed per-query failure
            continue
        for result in results:
            celex = result.get("celex", "")
            if celex and celex not in seen:
                documents.append(
                    {
                        "celex": celex,
                        "title": result.get("title", ""),
                        "date": result.get("date"),
                        "type": result.get("type"),
                        "source": name,
                    }
                )
                seen.add(celex)
    return {
        "source_id": "eurlex",
        "method_used": "SPARQL",
        "documents": [legacy_eurlex_normalize(d, designer=designer) for d in documents],
        "success": True,
        "error": None,
        "fallback_used": False,
    }


def legacy_update_query(profile: SourceProfile, since: datetime) -> str:
    """``check_for_updates`` query text of auditdatabase."""
    if profile.eurlex_update_query_template is None:
        raise ValueError("Profil ohne Aktualisierungsabfrage")
    return profile.eurlex_update_query_template.replace("{since}", since.strftime("%Y-%m-%d"))


# ---------------------------------------------------------------------------
# DIP (designer)
# ---------------------------------------------------------------------------


def designer_dip_drucksache(item: Mapping[str, Any], query: str) -> dict[str, Any] | None:
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


def designer_dip_vorgang(item: Mapping[str, Any], query: str) -> dict[str, Any] | None:
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


# ---------------------------------------------------------------------------
# RSS / publication pages (auditdatabase rss.py)
# ---------------------------------------------------------------------------


def _legacy_entry_parts(entry: Mapping[str, Any]) -> tuple[str, str, str, Any]:
    title = entry.get("title", "Ohne Titel")
    link = entry.get("link", "")
    summary = entry.get("summary", entry.get("description", ""))
    published = entry.get("published", entry.get("updated", ""))
    return title, link, summary, published


def legacy_bafin_entry(entry: Mapping[str, Any], feed_name: str) -> dict[str, Any] | None:
    """``BaFinHarvester._normalize_entry``; ``hash()`` identities depend on PYTHONHASHSEED."""
    try:
        title, link, summary, published = _legacy_entry_parts(entry)
        entry_id = link.split("/")[-1] if link else str(hash(title))
        pub_date: Any = ""
        if published:
            try:
                parsed = entry.get("published_parsed")
                if parsed:
                    pub_date = datetime(*parsed[:6]).isoformat()
            except Exception:  # noqa: BLE001 - reproduces the bare except
                pub_date = published
        return {
            "id": f"bafin_{entry_id}",
            "title": title,
            "document_type": f"BaFin {feed_name.title()}",
            "source": "bafin",
            "source_url": link,
            "funding_period": "2021-2027",
            "fund": "EFRE",
            "published_date": pub_date,
            "metadata": {
                "feed": feed_name,
                "categories": [tag["term"] for tag in entry.get("tags", [])],
            },
            "content": f"{title}\n\n{summary}",
        }
    except Exception:  # noqa: BLE001
        return None


def legacy_curia_entry(entry: Mapping[str, Any], feed_name: str) -> dict[str, Any] | None:
    """``CURIAHarvester._normalize_entry`` (only ``C-`` cases; type ``Urteil`` never reached)."""
    import re

    try:
        title, link, summary, published = _legacy_entry_parts(entry)
        match = re.search(r"C-\d+/\d+", title + summary)
        case_number = match.group(0) if match else ""
        entry_id = (case_number or link.split("/")[-1]) if link else str(hash(title))
        return {
            "id": f"curia_{entry_id}",
            "title": title,
            "document_type": "Urteil" if feed_name == "urteile" else "Pressemitteilung",
            "source": "curia",
            "source_url": link,
            "funding_period": "2021-2027",
            "fund": "EFRE",
            "published_date": published,
            "metadata": {"feed": feed_name, "case_number": case_number},
            "content": f"{title}\n\n{summary}",
        }
    except Exception:  # noqa: BLE001
        return None


#: Placeholder "core reports" the source returned as successful documents when
#: no ECA page could be read. They are not real publications (LS-C13).
LEGACY_ECA_PLACEHOLDERS = (
    (
        "eca_sr_2024_cohesion",
        "Sonderbericht: Kohäsionspolitik 2021-2027 - Vereinfachung und Leistungsorientierung",
        "Sonderbericht",
        "ECA Sonderbericht zur Kohäsionspolitik der Förderperiode 2021-2027",
    ),
    (
        "eca_sr_2023_erdf",
        "Sonderbericht: EFRE-Förderung - Wirksamkeit und Wirtschaftlichkeit",
        "Sonderbericht",
        "ECA Sonderbericht zur EFRE-Förderung",
    ),
    (
        "eca_annual_2023",
        "Jahresbericht 2023 zum EU-Haushalt",
        "Jahresbericht",
        "Jahresbericht des Europäischen Rechnungshofs zum EU-Haushalt 2023",
    ),
)


def legacy_eca_core_reports() -> list[dict[str, Any]]:
    """``ECAHarvester._get_core_reports`` placeholders, marked as such only in this adapter."""
    return [
        {
            "id": identifier,
            "title": title,
            "document_type": kind,
            "source": "eca",
            "source_url": "https://www.eca.europa.eu/de/publications",
            "funding_period": "2021-2027",
            "fund": "EFRE",
            "content": content,
        }
        for identifier, title, kind, content in LEGACY_ECA_PLACEHOLDERS
    ]
