"""Value extraction for TED notice fields (text, lists, amounts, dates).

Behavior-preserving part of ``audit_prep.ted_normalize`` from
``janpow77/audit-portal@d8eefa4``; :mod:`auditcore_procurement.ted` re-exports
every public name.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime

LANGUAGE_PREFERENCE = ("deu", "ger", "de", "eng", "en")


def first_present(notice: Mapping[str, object], aliases: Sequence[str]) -> object:
    for key in aliases:
        if key in notice:
            value = notice[key]
            if value is not None and value != "" and value != [] and value != {}:
                return value
    return None


def extract_text(value: object) -> str | None:
    """Single text from a scalar, list (first filled) or language dict (preference order)."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        return _language_text(value)
    if isinstance(value, list):
        return _first_text(value)
    return None


def _language_text(value: Mapping[object, object]) -> str | None:
    """Text in :data:`LANGUAGE_PREFERENCE` order, else the first filled value."""
    for language in LANGUAGE_PREFERENCE:
        if language in value:
            text = extract_text(value[language])
            if text:
                return text
    return _first_text(value.values())


def _first_text(items: Iterable[object]) -> str | None:
    """First item that yields a non-empty text."""
    for item in items:
        text = extract_text(item)
        if text:
            return text
    return None


def extract_list(value: object) -> list[str]:
    """Flat, de-duplicated list of strings; objects contribute ``code``/``value``/``id``."""
    result: list[str] = []

    def add(item: object) -> None:
        """Append the item's text once."""
        text = extract_text(item)
        if text and text not in result:
            result.append(text)

    if value is None:
        return result
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                code = item.get("code") or item.get("value") or item.get("id")
                add(code if code is not None else item)
            else:
                add(item)
    elif isinstance(value, dict):
        code = value.get("code") or value.get("value") or value.get("id")
        if code is not None:
            add(code)
        else:
            for item in value.values():
                add(item)
    else:
        add(value)
    return result


def extract_amount(value: object) -> tuple[float | None, str | None]:
    """(amount, currency) from scalar, amount object or list (largest amount).

    Legacy semantics: text amounts drop every comma (``"1,234.56"`` → 1234.56),
    so a German ``"1.234,56"`` becomes 1.23456. :func:`inspect_notice` reports
    such ambiguous inputs; the value itself is kept for compatibility.
    """
    if value is None:
        return None, None
    if isinstance(value, bool):
        return float(value), None
    if isinstance(value, (int, float)):
        return float(value), None
    if isinstance(value, str):
        try:
            return float(value.strip().replace(",", "")), None
        except ValueError:
            return None, None
    if isinstance(value, dict):
        raw = value.get("amount") if value.get("amount") is not None else value.get("value")
        currency = value.get("currency") or value.get("currencyCode")
        amount, _ = extract_amount(raw)
        return amount, (str(currency) if currency else None)
    if isinstance(value, list):
        best: float | None = None
        best_currency: str | None = None
        for item in value:
            amount, currency = extract_amount(item)
            if amount is not None and (best is None or amount > best):
                best, best_currency = amount, currency
        return best, best_currency
    return None, None


def to_iso_date(value: object) -> str | None:
    """``YYYY-MM-DD`` from TED dates with offsets/time suffix or common layouts, else None."""
    text = extract_text(value)
    if not text:
        return None
    candidate = text.strip()
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", candidate)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    for layout in ("%Y%m%d", "%d/%m/%Y", "%d.%m.%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(candidate, layout).date().isoformat()
        except ValueError:
            continue
    return None
