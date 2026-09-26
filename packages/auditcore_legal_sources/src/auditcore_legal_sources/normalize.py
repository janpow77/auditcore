"""Normalization helpers: publication dates, classification rules, deduplication.

Classification rules are named after the application they were characterized
from; the variants differ (see ``docs/behavior-changes.md``) and are not merged.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date, datetime

from .model import LegalDocument, as_date

_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:[T ].*)?$")
_ISO_MONTH = re.compile(r"^(\d{4})-(\d{2})$")
_GERMAN = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$")
_YEAR = re.compile(r"^(\d{4})$")


def parse_publication_date(value: object) -> tuple[date | None, str | None]:
    """Parse ISO date/datetime, ``YYYY-MM``, ``DD.MM.YYYY`` or ``YYYY``.

    Returns the date and its precision (``day``, ``month``, ``year``) or
    ``(None, None)`` for missing or invalid values. The source applications
    returned ``None`` for every string (defect LS-C01).
    """
    if isinstance(value, (date, datetime)):
        return as_date(value), "day"
    if not isinstance(value, str) or not value.strip():
        return None, None
    text = value.strip()
    try:
        if match := _ISO.match(text):
            return date(int(match[1]), int(match[2]), int(match[3])), "day"
        if match := _ISO_MONTH.match(text):
            return date(int(match[1]), int(match[2]), 1), "month"
        if match := _GERMAN.match(text):
            return date(int(match[3]), int(match[2]), int(match[1])), "day"
        if match := _YEAR.match(text):
            return date(int(match[1]), 1, 1), "year"
    except ValueError:
        return None, None
    return None, None


def funding_period_auditdatabase(text: str | None) -> str | None:
    """Funding period rule of auditdatabase ``BaseHarvester._detect_funding_period``."""
    if not text:
        return None
    lower = text.lower()
    if "2021/1060" in text or "2021-2027" in lower or "dachverordnung" in lower:
        return "2021-2027"
    if "1303/2013" in text or "2014-2020" in lower:
        return "2014-2020"
    return None


#: Period names searched in the text, in the order of the source rule.
_DESIGNER_PERIOD_NAMES = ("2021-2027", "2014-2020", "2007-2013", "2000-2006", "1994-1999")
#: Regulation numbers per period, in the order of the source rule.
_DESIGNER_PERIOD_REGULATIONS = (
    ("2000-2006", ("1260/1999", "1783/1999", "2081/93")),
    ("2007-2013", ("1083/2006", "1080/2006", "1081/2006")),
    ("2014-2020", ("1303/2013", "1301/2013", "1304/2013")),
    ("2021-2027", ("2021/1060", "2021/1057", "2021/1058")),
)
#: First year of each period, newest first.
_DESIGNER_PERIOD_STARTS = (
    (2021, "2021-2027"),
    (2014, "2014-2020"),
    (2007, "2007-2013"),
    (2000, "2000-2006"),
    (1994, "1994-1999"),
)


def _designer_period_from_text(text: str) -> str | None:
    lower = text.lower()
    for period in _DESIGNER_PERIOD_NAMES:
        if period in lower:
            return period
    for period, numbers in _DESIGNER_PERIOD_REGULATIONS:
        if any(n in text for n in numbers):
            return period
    if "dachverordnung" in lower:
        return "2021-2027"
    return None


def _designer_period_from_year(publication_date: str) -> str | None:
    try:
        year = int(str(publication_date)[:4])
    except (ValueError, TypeError):
        return None
    for start, period in _DESIGNER_PERIOD_STARTS:
        if year >= start:
            return period
    return None


def funding_period_designer(text: str | None, publication_date: str | None = None) -> str | None:
    """Funding period rule of audit_designer ``_funding_period.detect_funding_period``."""
    if text:
        period = _designer_period_from_text(text)
        if period is not None:
            return period
    if publication_date:
        return _designer_period_from_year(publication_date)
    return None


def detect_fund(text: str | None) -> str | None:
    """Fund keyword rule; identical in both characterized applications."""
    if not text:
        return None
    upper = text.upper()
    if "EFRE" in upper or "ERDF" in upper:
        return "EFRE"
    if "ESF+" in upper or "ESF PLUS" in upper:
        return "ESF+"
    if "ESF" in upper:
        return "ESF"
    if "KOHÄSION" in upper or "COHESION" in upper:
        return "KF"
    return None


def is_relevant(text: str | None, keywords: Iterable[str]) -> bool:
    """Case-insensitive substring match against explicitly supplied keywords."""
    if not text:
        return False
    lower = text.lower()
    return any(keyword.lower() in lower for keyword in keywords)


def deduplicate(documents: Iterable[LegalDocument]) -> tuple[list[LegalDocument], list[str]]:
    """Keep the first document per identity; returns kept documents and dropped identities."""
    seen: set[str] = set()
    kept: list[LegalDocument] = []
    dropped: list[str] = []
    for document in documents:
        if document.identity in seen:
            dropped.append(document.identity)
            continue
        seen.add(document.identity)
        kept.append(document)
    return kept, dropped
