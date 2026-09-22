"""TED notice normalisation, file import and query building (pure, no network).

Behavior-preserving extraction of ``audit_prep.ted_normalize`` and the query
part of ``app/services/ted_harvester_service.py`` from
``janpow77/audit-portal@d8eefa4``. Online harvest (via ``auditcore_harvest``)
and file import produce the same canonical record contract
(:mod:`auditcore_procurement.records`).

Coverage: the default query and :func:`normalize_notice` only yield **award
notices with a named contractor** (``notice-type=can-standard AND
winner-name=*``). That is the source application's purpose (supplier/invoice
matching), not full TED coverage; results carry :data:`COVERAGE_AWARDS_WITH_WINNER`.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from .records import COVERAGE_ALL_NOTICES, COVERAGE_AWARDS_WITH_WINNER, Issue

#: Target field → candidate keys in a TED notice (priority order). The key order
#: is the column order of :func:`parse_ted_file` and must stay stable.
FIELD_ALIASES: dict[str, list[str]] = {
    "notice_id": ["publication-number", "ND", "noticePublicationNumber"],
    "contract_id": ["contract-identifier", "contract-id"],
    "document_number": ["document-number", "ND", "publication-number"],
    "contracting_authority_name": [
        "buyer-name",
        "organisation-name-buyer",
        "official-name-buyer",
        "AA_NAME",
    ],
    "contracting_authority_country": [
        "buyer-country",
        "organisation-country-buyer",
        "country-buyer",
        "CY",
    ],
    "contracting_authority_address": ["buyer-address", "organisation-address-buyer"],
    "contractor_name": [
        "winner-name",
        "organisation-name-serv-prov",
        "winner-official-name",
        "tenderer-name",
        "WIN_NAME",
    ],
    "contractor_country": ["winner-country", "organisation-country-serv-prov", "tenderer-country"],
    "contractor_address": ["winner-address", "organisation-address-serv-prov"],
    "contractor_vat_id": [
        "winner-identifier",
        "organisation-identifier-tenderer",
        "organisation-identifier-serv-prov",
        "winner-nationalid",
    ],
    "title": ["notice-title", "title-proc", "title", "TI"],
    "description": ["description-proc", "description", "short-descr"],
    "cpv_codes": ["classification-cpv", "main-classification-proc", "cpv", "CPV"],
    "nuts_codes": ["place-performance-nuts", "performance-nuts", "nuts", "RC"],
    "contract_value": [
        "result-value-notice",
        "result-value-lot",
        "winner-value",
        "tender-value",
        "notice-value",
    ],
    "contract_value_currency": [
        "result-value-cur-notice",
        "result-value-cur-lot",
        "currency",
        "value-currency",
    ],
    "estimated_value": ["estimated-value-proc", "estimated-value-lot", "estimated-value"],
    "publication_date": ["publication-date", "dispatch-date", "PD"],
    "contract_award_date": [
        "winner-decision-date",
        "contract-conclusion-date",
        "award-date",
        "DT_AWARD",
    ],
    "contract_start_date": ["contract-start-date", "duration-start"],
    "contract_end_date": ["contract-end-date", "duration-end"],
    "procedure_type": ["procedure-type", "type-procedure", "PR_PROC"],
    "contract_type": [
        "contract-nature",
        "main-nature-proc",
        "nature-proc",
        "NC_CONTRACT_NATURE",
    ],
}

LIST_FIELDS = frozenset({"cpv_codes", "nuts_codes"})
DATE_FIELDS = frozenset(
    {"publication_date", "contract_award_date", "contract_start_date", "contract_end_date"}
)
NUMBER_FIELDS = frozenset({"contract_value", "estimated_value"})
LANGUAGE_PREFERENCE = ("deu", "ger", "de", "eng", "en")

#: Field set requested from the TED search API v3 (validated against live TED
#: by the source application; unknown field codes are rejected with HTTP 400).
DEFAULT_FIELDS: tuple[str, ...] = (
    "publication-number",
    "notice-title",
    "publication-date",
    "classification-cpv",
    "buyer-name",
    "buyer-country",
    "winner-name",
    "winner-country",
    "winner-identifier",
    "winner-decision-date",
    "result-value-notice",
    "result-value-cur-notice",
    "procedure-type",
    "contract-nature",
)
AWARD_FILTER = ("notice-type=can-standard", "winner-name=*")


def _first_present(notice: Mapping[str, Any], aliases: Sequence[str]) -> Any:
    for key in aliases:
        if key in notice:
            value = notice[key]
            if value is not None and value != "" and value != [] and value != {}:
                return value
    return None


def extract_text(value: Any) -> str | None:
    """Single text from a scalar, list (first filled) or language dict (preference order)."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        for language in LANGUAGE_PREFERENCE:
            if language in value:
                text = extract_text(value[language])
                if text:
                    return text
        for candidate in value.values():
            text = extract_text(candidate)
            if text:
                return text
        return None
    if isinstance(value, list):
        for item in value:
            text = extract_text(item)
            if text:
                return text
    return None


def extract_list(value: Any) -> list[str]:
    """Flat, de-duplicated list of strings; objects contribute ``code``/``value``/``id``."""
    result: list[str] = []

    def add(item: Any) -> None:
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


def extract_amount(value: Any) -> tuple[float | None, str | None]:
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


def to_iso_date(value: Any) -> str | None:
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


def normalize_notice(notice: Any, *, require_contractor: bool = True) -> dict[str, Any] | None:
    """Flat canonical record of one TED notice.

    With ``require_contractor=True`` (source behavior) notices without a
    contractor name return ``None``. ``False`` keeps them for callers that
    need all notice types; such records have no ``contractor_name``.
    """
    if not isinstance(notice, dict):
        return None
    record: dict[str, Any] = {}
    amount, amount_currency = extract_amount(
        _first_present(notice, FIELD_ALIASES["contract_value"])
    )
    estimated, _ = extract_amount(_first_present(notice, FIELD_ALIASES["estimated_value"]))
    for field, aliases in FIELD_ALIASES.items():
        if field in ("contract_value", "estimated_value", "contract_value_currency"):
            continue
        raw = _first_present(notice, aliases)
        if raw is None:
            continue
        if field in LIST_FIELDS:
            items = extract_list(raw)
            if items:
                record[field] = ", ".join(items)
        elif field in DATE_FIELDS:
            iso = to_iso_date(raw)
            if iso:
                record[field] = iso
        else:
            text = extract_text(raw)
            if text:
                record[field] = text
    if amount is not None:
        record["contract_value"] = amount
    if estimated is not None:
        record["estimated_value"] = estimated
    currency = amount_currency or extract_text(
        _first_present(notice, FIELD_ALIASES["contract_value_currency"])
    )
    if currency:
        record["contract_value_currency"] = currency
    if require_contractor and not record.get("contractor_name"):
        return None
    return record


def normalize_notices(
    raw_notices: Sequence[Any], *, require_contractor: bool = True
) -> list[dict[str, Any]]:
    """Normalise a list of notices; ``None`` results are skipped."""
    records: list[dict[str, Any]] = []
    for notice in raw_notices:
        normalized = normalize_notice(notice, require_contractor=require_contractor)
        if normalized is not None:
            records.append(normalized)
    return records


def parse_ted_file(
    file_bytes: bytes, file_name: str
) -> tuple[list[dict[str, Any]], list[str], dict[str, list[str]]]:
    """Parse a TED JSON upload (raw v3 notices or already normalised records).

    Returns ``(records, columns, validation)`` exactly like the source; only
    award notices with ``contractor_name`` are kept. ``file_name`` is accepted
    for interface compatibility (the source used it for logging only).
    """
    del file_name
    validation: dict[str, list[str]] = {"errors": [], "warnings": []}
    columns = list(FIELD_ALIASES.keys())
    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1")
        validation["warnings"].append("Datei nicht UTF-8-kodiert — Latin-1-Fallback verwendet.")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        validation["errors"].append(
            "TED-Datei ist kein gültiges JSON — erwartet wird ein JSON-Array "
            "von TED-Notices (roh oder normalisiert)."
        )
        return [], columns, validation
    if isinstance(data, dict):
        data = data.get("notices") or data.get("results") or data.get("data") or []
    if not isinstance(data, list):
        validation["errors"].append("TED-JSON enthält kein Array von Notices.")
        return [], columns, validation
    notices = [n for n in data if isinstance(n, dict)]
    if notices and "contractor_name" in notices[0]:
        records = [n for n in notices if n.get("contractor_name")]
    else:
        records = normalize_notices(notices)
    skipped = len(notices) - len(records)
    if skipped:
        validation["warnings"].append(
            f"{skipped} Notice(s) ohne Auftragnehmer (contractor_name) übersprungen."
        )
    if not records:
        validation["errors"].append(
            "Die Datei enthält keine verwertbaren TED-Zuschläge "
            "(Zuschlagsbekanntmachung mit contractor_name)."
        )
    return records, columns, validation


def dump_records(records: Sequence[Mapping[str, Any]]) -> bytes:
    """Serialise normalised records as the JSON array the file import reads back."""
    return json.dumps(list(records), ensure_ascii=False).encode("utf-8")


def to_ted_date(value: Any) -> str:
    """``YYYYMMDD`` for date/datetime/ISO text; unparseable input is passed through as text."""
    if hasattr(value, "strftime"):
        return str(value.strftime("%Y%m%d"))
    iso = to_iso_date(value)
    if iso:
        return iso.replace("-", "")
    return str(value)


def build_ted_query(
    *,
    query: str | None = None,
    cpv_codes: Sequence[str] | None = None,
    country: str | None = None,
    contractor_name: str | None = None,
    date_from: Any = None,
    date_to: Any = None,
) -> str:
    """TED expert query. An explicit ``query`` wins; otherwise filters are AND-combined
    and always restricted to award notices with a winner (:data:`AWARD_FILTER`)."""
    if query and query.strip():
        return query.strip()
    clauses: list[str] = []
    if cpv_codes:
        cpv_or = " OR ".join(f"classification-cpv={c.strip()}" for c in cpv_codes if c.strip())
        if cpv_or:
            clauses.append(f"({cpv_or})")
    if country:
        clauses.append(f"buyer-country={country.strip()}")
    if contractor_name:
        clauses.append(f'winner-name="{contractor_name.strip()}"')
    if date_from is not None:
        clauses.append(f"publication-date>={to_ted_date(date_from)}")
    if date_to is not None:
        clauses.append(f"publication-date<={to_ted_date(date_to)}")
    clauses.extend(AWARD_FILTER)
    return " AND ".join(clauses)


def query_coverage(query: str | None) -> str:
    """Coverage label of a query built by :func:`build_ted_query`."""
    if query and query.strip():
        text = query.strip()
        return (
            COVERAGE_AWARDS_WITH_WINNER
            if all(f in text for f in AWARD_FILTER)
            else (COVERAGE_ALL_NOTICES)
        )
    return COVERAGE_AWARDS_WITH_WINNER


_GERMAN_AMOUNT = re.compile(r"^\s*-?\d{1,3}(\.\d{3})+(,\d+)?\s*$|^\s*-?\d+,\d{1,2}\s*$")


def _amount_texts(raw: Any) -> list[Any]:
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, dict):
        return [raw.get("amount")]
    if isinstance(raw, list):
        return [item.get("amount") if isinstance(item, dict) else item for item in raw]
    return []


def inspect_notice(notice: Any) -> list[Issue]:
    """Visible warnings the legacy normalisation does not report (never alters records).

    ``ambiguous_amount``: German decimal comma text; ``unparsed_amount``: text
    amount that yields no number; ``unparsed_date``; ``no_contractor``;
    ``correction_notice``: change/correction markers are not modelled by the
    source contract (``notice-type`` ``corr``, ``change-notice-version-identifier``).
    """
    if not isinstance(notice, dict):
        return [Issue("not_a_notice", "Eintrag ist kein TED-Notice-Objekt.", True)]
    issues: list[Issue] = []
    for field in ("contract_value", "estimated_value"):
        raw = _first_present(notice, FIELD_ALIASES[field])
        texts = _amount_texts(raw)
        for text in texts:
            if not isinstance(text, str):
                continue
            if _GERMAN_AMOUNT.match(text):
                issues.append(
                    Issue(
                        "ambiguous_amount",
                        f"{field}: '{text}' ist mehrdeutig "
                        "(Dezimalkomma); der Altvertrag entfernt Kommas.",
                        True,
                        field,
                    )
                )
            elif extract_amount(text)[0] is None:
                issues.append(
                    Issue("unparsed_amount", f"{field}: '{text}' ist keine Zahl.", False, field)
                )
    for field in DATE_FIELDS:
        raw = _first_present(notice, FIELD_ALIASES[field])
        if raw is not None and to_iso_date(raw) is None:
            issues.append(Issue("unparsed_date", f"{field}: Datum nicht lesbar.", False, field))
    if not extract_text(_first_present(notice, FIELD_ALIASES["contractor_name"])):
        issues.append(
            Issue(
                "no_contractor",
                "Keine Zuschlagsbekanntmachung mit Auftragnehmer.",
                False,
                "contractor_name",
            )
        )
    if str(notice.get("notice-type") or "").startswith("corr") or notice.get(
        "change-notice-version-identifier"
    ):
        issues.append(
            Issue(
                "correction_notice",
                "Berichtigung/Änderungsbekanntmachung: der "
                "Bezug zur Ursprungsfassung wird nicht abgebildet.",
                False,
            )
        )
    return issues
