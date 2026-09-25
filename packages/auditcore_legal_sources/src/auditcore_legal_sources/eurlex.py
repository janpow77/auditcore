"""EUR-Lex/Cellar SPARQL request and result contract.

Pure functions: SPARQL form parameters, strict parsing of the W3C
``application/sparql-results+json`` format, CELEX document types, profile
core documents, merge of query results and normalization. HTTP, retries and
checkpoints belong to the ``auditcore_harvest`` engine.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from .errors import ConfigurationError, ParseError
from .model import LegalDocument
from .normalize import (
    detect_fund,
    funding_period_auditdatabase,
    funding_period_designer,
    parse_publication_date,
)
from .profile import SourceProfile

SOURCE_ID = "eurlex"
RESULTS_MEDIA_TYPE = "application/sparql-results+json"


def sparql_form(query: str) -> dict[str, str]:
    """Form body of a SPARQL 1.1 protocol POST request."""
    if not isinstance(query, str) or not query.strip():
        raise ConfigurationError("SPARQL-Abfrage fehlt.")
    return {"query": query, "format": RESULTS_MEDIA_TYPE}


def update_query(profile: SourceProfile, since: date) -> str:
    """Incremental query of the profile; ``since`` must be a date (no text injection)."""
    if profile.eurlex_update_query_template is None:
        raise ConfigurationError(f"Profil {profile.id} hat keine Aktualisierungsabfrage.")
    if not isinstance(since, date):
        raise ConfigurationError("Das Startdatum muss ein Datum sein.")
    return profile.eurlex_update_query_template.replace("{since}", since.isoformat())


def parse_results(payload: object) -> list[dict[str, str]]:
    """Flatten ``results.bindings`` to ``{variable: value}`` rows.

    Raises:
        ParseError: the payload is not a SPARQL JSON result set.
    """
    if not isinstance(payload, Mapping) or not isinstance(payload.get("results"), Mapping):
        raise ParseError("Keine SPARQL-JSON-Ergebnismenge.", source_id=SOURCE_ID)
    bindings = payload["results"].get("bindings")
    if not isinstance(bindings, list):
        raise ParseError(
            "SPARQL-Ergebnis ohne bindings.", source_id=SOURCE_ID, location="results.bindings"
        )
    rows = []
    for index, binding in enumerate(bindings):
        if not isinstance(binding, Mapping):
            raise ParseError(
                "Ungültiger SPARQL-Binding-Eintrag.",
                source_id=SOURCE_ID,
                location=f"results.bindings[{index}]",
            )
        row = {}
        for variable, value in binding.items():
            if not isinstance(value, Mapping) or not isinstance(value.get("value"), str):
                raise ParseError(
                    "SPARQL-Wert ohne value.",
                    source_id=SOURCE_ID,
                    location=f"results.bindings[{index}].{variable}",
                )
            row[str(variable)] = str(value["value"])
        rows.append(row)
    return rows


def celex_document_type(celex: str) -> str:
    """Document type from the CELEX sector/type letters (source rule)."""
    if not celex:
        return "Unbekannt"
    if celex.startswith("3"):
        for letter, label in (("R", "Verordnung"), ("L", "Richtlinie"), ("D", "Beschluss")):
            if letter in celex:
                return label
    elif celex.startswith("5"):
        return "Guidance"
    elif celex.startswith("6"):
        return "Rechtsprechung"
    return "Sonstiges"


def core_rows(profile: SourceProfile) -> list[dict[str, str]]:
    """Core documents of the profile as rows (always included first)."""
    return [
        {"celex": d.celex, "title": d.title, "funding_period": d.period, "source": "core_documents"}
        for d in profile.eurlex_core_documents
    ]


def merge_rows(
    profile: SourceProfile, query_rows: Mapping[str, Sequence[Mapping[str, str]]]
) -> list[dict[str, str]]:
    """Core documents, then query rows in profile order; first occurrence per CELEX wins.

    Rows without CELEX are skipped exactly like the sources did; the caller
    reports failed queries separately (they are not an empty result).
    """
    merged = core_rows(profile)
    seen = {row["celex"] for row in merged}
    for name in profile.eurlex_queries:
        for row in query_rows.get(name, ()):
            celex = row.get("celex", "")
            if celex and celex not in seen:
                merged.append(
                    {
                        "celex": celex,
                        "title": row.get("title", ""),
                        "date": row.get("date", ""),
                        "type": row.get("type", ""),
                        "source": name,
                    }
                )
                seen.add(celex)
    return merged


def normalize_row(row: Mapping[str, str], profile: SourceProfile) -> LegalDocument:
    """Normalize one merged row; the publication date is actually parsed (LS-C01).

    Raises:
        ParseError: row without CELEX number.
    """
    celex = row.get("celex") or ""
    if not celex:
        raise ParseError("EUR-Lex-Eintrag ohne CELEX-Nummer.", source_id=SOURCE_ID)
    title = row.get("title") or ""
    rule = (
        funding_period_designer
        if profile.eurlex_funding_period_rule == "designer"
        else funding_period_auditdatabase
    )
    period = row.get("funding_period") or rule(f"{celex} {title}")
    published, precision = parse_publication_date(row.get("date") or "")
    return LegalDocument(
        source_id=SOURCE_ID,
        external_id=celex,
        title=title,
        publication_date=published,
        date_precision=precision,
        raw_date=row.get("date") or None,
        source_url=f"{profile.eurlex_document_url}{celex}",
        document_type=celex_document_type(celex),
        language="de",
        classification={
            "funding_period": period,
            "fund": detect_fund(title),
            "rule": profile.eurlex_funding_period_rule,
        },
        metadata={
            "celex": celex,
            "query_source": row.get("source"),
            "raw_type": row.get("type") or None,
        },
        profile=profile.reference,
        adapter="eurlex.sparql",
    )
