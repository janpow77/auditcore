"""Shared legacy helpers: date parsing, detection rules and the harvested-document shape."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from datetime import datetime

from auditcore_harvest import JSON

from ..normalize import detect_fund, funding_period_auditdatabase, funding_period_designer

_LEGACY_FORMATS = ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d.%m.%Y", "%Y")


def legacy_parse_date(value: object) -> datetime | None:
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


def legacy_harvested_document(source_id: str, **fields: JSON) -> dict[str, JSON]:
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


def legacy_normalize_document(source_id: str, raw: Mapping[str, JSON]) -> dict[str, JSON]:
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
