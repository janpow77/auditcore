"""``duplicates``: exact and fuzzy invoice duplicates among pre-selected candidates.

The application keeps its SQL window and limit; these functions compare the
candidate documents it has already selected.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from .base import JsonObject
from .errors import InputError, ProfileError
from .fraud_profile import FraudProfile, require_parameters
from .values import is_missing


@dataclass(frozen=True)
class DuplicateMatch:
    """One candidate document considered a duplicate."""

    candidate_id: Any
    match_type: str
    confidence: float
    details: JsonObject


def _decimal(value: object, where: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, int | float | str | Decimal):
        raise InputError(f"{where}: Betrag als Zahl oder Text erwartet.")
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise InputError(f"{where}: kein Betrag {value!r}.") from exc


def exact_duplicates(
    invoice: JsonObject, candidates: Iterable[JsonObject], profile: FraudProfile
) -> list[DuplicateMatch]:
    """Same invoice number (candidate side not trimmed) and amount difference below the limit."""
    p = require_parameters(profile, "duplicates")["exact"]
    number = str(invoice["invoice_number"])
    wanted = number.strip().upper()
    total = _decimal(invoice["total_amount"], "total_amount")
    out = []
    for cand in candidates:
        cand_number = cand.get("invoice_number")
        if is_missing(cand_number) or str(cand_number).upper() != wanted:
            continue
        try:
            amount = Decimal(_cleaned_amount(cand.get("gross_amount"), p))
        except InvalidOperation:
            amount = Decimal(p["invalid_amount"])
        if abs(amount - total) < Decimal(p["tolerance"]):
            out.append(
                DuplicateMatch(
                    cand.get("id"),
                    "exact",
                    float(p["confidence"]),
                    {
                        "invoice_number": number,
                        "amount": str(total),
                        "original_filename": cand.get("original_filename"),
                        "original_project_id": cand.get("project_id"),
                    },
                )
            )
    return out


def names_similar(first: str, second: str, min_containment: int, leading_words: int) -> bool:
    """Legacy name heuristic: equal, containment (≥ ``min_containment``) or a shared word
    among the first ``leading_words`` words (very permissive; see RK-L)."""
    if first == second:
        return True
    if len(first) >= min_containment and first in second:
        return True
    if len(second) >= min_containment and second in first:
        return True
    a, b = first.split()[:leading_words], second.split()[:leading_words]
    return bool(a and b and set(a) & set(b))


def parse_date(value: str, formats: Sequence[str]) -> date | None:
    """First matching format wins (European before US for ambiguous dates)."""
    if not value:
        return None
    text = value.strip()
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _cleaned_amount(raw: object, p: JsonObject) -> str:
    """Candidate amount text after the source's replacements (missing → substitute)."""
    cleaned = str(p["missing_amount"] if raw is None else raw)
    for old, new in p["amount_replacements"]:
        cleaned = cleaned.replace(old, new)
    return cleaned


def _invoice_day(invoice: JsonObject) -> date:
    day = invoice["invoice_date"]
    if isinstance(day, str):
        day = date.fromisoformat(day)
    if not isinstance(day, date):
        raise InputError("invoice_date muss ein Datum sein.")
    return day


def _fuzzy_match(
    cand: JsonObject, cand_amount: float, cand_date: date, amount: float, day: date, p: JsonObject
) -> DuplicateMatch:
    """Match with the source's confidence (weighted amount and date distance)."""
    days = int(p["date_range_days"])
    cand_supplier = cand.get("supplier_name")
    cand_supplier = "" if cand_supplier is None else str(cand_supplier)
    amount_diff = abs(cand_amount - amount) / amount
    date_diff = abs((cand_date - day).days) / days
    confidence = 1.0 - (amount_diff * p["amount_weight"] + date_diff * p["date_weight"])
    return DuplicateMatch(
        cand.get("id"),
        "fuzzy",
        round(max(0.0, min(1.0, confidence)), int(p["digits"])),
        {
            "supplier_name": cand_supplier[: int(p["name_chars"])],
            "amount": f"{cand_amount:.2f}",
            "date": str(cand_date),
            "amount_diff_percent": f"{amount_diff * 100:.1f}%",
            "original_filename": cand.get("original_filename"),
            "original_project_id": cand.get("project_id"),
        },
    )


def _candidate_date(cand: JsonObject, p: JsonObject) -> date | None:
    raw = cand.get("invoice_date")
    return parse_date("" if raw is None else str(raw), p["date_formats"])


def _similar_supplier(cand: JsonObject, supplier: str, p: JsonObject) -> bool:
    cand_supplier = cand.get("supplier_name")
    name = "" if cand_supplier is None else str(cand_supplier)
    return names_similar(supplier, name.lower(), int(p["min_containment"]), int(p["leading_words"]))


def fuzzy_duplicates(
    invoice: JsonObject, candidates: Iterable[JsonObject], profile: FraudProfile
) -> list[DuplicateMatch]:
    """Amount within ±tolerance, date within ±days and similar supplier name."""
    p = require_parameters(profile, "duplicates")["fuzzy"]
    amount = float(_decimal(invoice["total_amount"], "total_amount"))
    if amount == 0:
        raise InputError("Fuzzy-Abgleich mit Betrag 0 ist nicht definiert (Quelle: Division).")
    tolerance = float(p["amount_tolerance"])
    days = int(p["date_range_days"])
    low, high = amount * (1 - tolerance), amount * (1 + tolerance)
    day = _invoice_day(invoice)
    min_date, max_date = day - timedelta(days=days), day + timedelta(days=days)
    supplier = str(invoice["supplier_name"]).lower().strip()
    out = []
    for cand in candidates:
        try:
            cand_amount = float(_cleaned_amount(cand.get("gross_amount"), p))
        except ValueError:
            continue
        if not (low <= cand_amount <= high):
            continue
        cand_date = _candidate_date(cand, p)
        if cand_date is None or not (min_date <= cand_date <= max_date):
            continue
        if not _similar_supplier(cand, supplier, p):
            continue
        out.append(_fuzzy_match(cand, cand_amount, cand_date, amount, day, p))
    return out


def find_duplicates(
    invoice: JsonObject, candidates: Sequence[JsonObject], profile: FraudProfile
) -> list[DuplicateMatch]:
    """Exact matches first; fuzzy matches only if there is no exact match (as the source)."""
    exact = exact_duplicates(invoice, candidates, profile)
    return exact if exact else fuzzy_duplicates(invoice, candidates, profile)


def validate_duplicates(p: JsonObject) -> None:
    """Parameter contract of a ``duplicates`` profile."""
    if set(p) != {"exact", "fuzzy"}:
        raise ProfileError("duplicates braucht 'exact' und 'fuzzy'.")
    fuzzy = p["fuzzy"]
    if not 0 <= float(fuzzy["amount_tolerance"]) < 1 or int(fuzzy["date_range_days"]) <= 0:
        raise ProfileError("Toleranz oder Zeitfenster ungültig.")
    if not math.isclose(float(fuzzy["amount_weight"]) + float(fuzzy["date_weight"]), 1.0):
        raise ProfileError("Gewichte der Konfidenz müssen 1 ergeben.")
