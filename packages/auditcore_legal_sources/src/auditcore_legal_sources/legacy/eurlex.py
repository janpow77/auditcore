"""Legacy EUR-Lex flow of auditdatabase and audit_designer (``EURLexHarvester``)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from datetime import datetime
from typing import Any

from ..eurlex import celex_document_type
from ..profile import SourceProfile
from .common import (
    designer_detect_funding_period,
    legacy_detect_fund,
    legacy_detect_funding_period,
    legacy_harvested_document,
    legacy_parse_date,
)


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
