"""Source profile ``flowworkshop.beneficiaries``: parsers, identity and snapshot checks.

Behavior of ``janpow77/flowworkshop@a05bb21``
(``services/beneficiary_harvester.py``, ``services/state_aid_service.py``),
reproduced exactly and verified against recorded outputs. Hash fields,
``None``/NaN semantics and the validation thresholds are unchanged: changing
them would change the identity of stored records.

The table readers live in :mod:`auditcore_funding_sources.tables`; this module
maps table rows to beneficiary rows exactly like ``parse_xlsx_or_csv``.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from .profiles import load_profile

PROFILE_ID = "flowworkshop.beneficiaries"
MODES = ("smart", "full-refresh", "force", "snapshot")

_ACCENT_TABLE = str.maketrans(
    {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "ae", "Ö": "oe", "Ü": "ue"}
)
_STRIP_TABLE = str.maketrans(
    {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        "Ä": "ae",
        "Ö": "oe",
        "Ü": "ue",
        "á": "a",
        "à": "a",
        "â": "a",
        "ã": "a",
        "å": "a",
        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",
        "í": "i",
        "ì": "i",
        "î": "i",
        "ï": "i",
        "ó": "o",
        "ò": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ù": "u",
        "û": "u",
        "ç": "c",
        "ñ": "n",
        "ý": "y",
        "ł": "l",
        "ń": "n",
        "ś": "s",
        "ź": "z",
        "ż": "z",
        "č": "c",
        "š": "s",
        "ž": "z",
        "đ": "d",
    }
)
_SA_REGEX = re.compile(r"\bSA[\s\.\-_]*(\d{4,6})(?:[/\-\.](\d{4}))?", re.IGNORECASE)
_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_ROLE_TO_ALIAS = (
    "name",
    "projekt",
    "aktenzeichen",
    "beschreibung",
    "kosten",
    "kosten_eu",
    "standort",
    "ort",
    "plz",
    "landkreis",
    "latitude",
    "longitude",
    "beginn",
    "ende",
)


def profile() -> dict[str, Any]:
    """The packaged source profile (column patterns, hash fields, thresholds)."""
    return load_profile(PROFILE_ID)


# ---------------------------------------------------------------------------
# state_aid_service: amount, date, names, SA references
# ---------------------------------------------------------------------------


def parse_amount(text: Any) -> Decimal | None:
    """Amount from a published string; ranges yield the upper bound.

    ``'1.200.000,00'`` and ``'1,200,000'`` are both understood; an unparsable
    value is ``None`` (never ``0``). A value with only dots such as ``'1.234.567'``
    is **not** understood (``None``) — unchanged source behavior, see
    ``docs/behavior-changes.md`` (FS-W05).
    """
    if text is None:
        return None
    s = str(text).strip()
    if not s or s in {"-", "—"}:
        return None
    s = re.sub(r"[€$£¥]", "", s)
    s = re.sub(r"\b(eur|usd|gbp|chf|sek)\b", "", s, flags=re.IGNORECASE).strip()
    m_range = re.search(r"(.+?)\s+to\s+(.+)", s, flags=re.IGNORECASE)
    if m_range:
        return parse_amount(m_range.group(2))
    m_lt = re.match(r"\s*(?:less than|<)\s*(.+)", s, flags=re.IGNORECASE)
    if m_lt:
        return parse_amount(m_lt.group(1))
    m_gt = re.match(r"\s*(?:more than|>)\s*(.+)", s, flags=re.IGNORECASE)
    if m_gt:
        return parse_amount(m_gt.group(1))
    s = re.sub(r"\s+", "", s)
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        left, _, right = s.rpartition(",")
        if len(right) in (1, 2) and right.isdigit():
            s = f"{left.replace(',', '')}.{right}"
        else:
            s = s.replace(",", "")
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def parse_date(text: Any) -> date | None:
    """``DD/MM/YYYY``, ``YYYY-MM-DD``, ``DD.MM.YYYY`` or ``YYYY/MM/DD``."""
    if not text:
        return None
    s = str(text).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def strip_accents(text: Any) -> str:
    """Diacritics and German umlauts folded for comparison."""
    if not text:
        return ""
    return str(text).translate(_STRIP_TABLE)


def normalize_company_name(text: Any, *, drop_filler: bool = False) -> str:
    """Comparison form: lower case, no accents, no legal-form suffix, compact spaces."""
    if not text:
        return ""
    data = profile()
    suffixes = set(data["legal_suffixes"])
    fillers = set(data["filler_words"])
    s = strip_accents(text).casefold()
    s = s.replace("&", " und ")
    s = _PUNCT_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    tokens: list[str] = []
    for tok in s.split():
        compact = tok.replace(".", "").replace("-", "")
        if compact in suffixes:
            continue
        if drop_filler and compact in fillers:
            continue
        tokens.append(tok)
    return " ".join(tokens)


def detect_sa_reference(text: Any) -> tuple[str | None, str | None]:
    """``(SA.12345[/2021], case URL)`` or ``(None, None)``."""
    if not text:
        return None, None
    m = _SA_REGEX.search(str(text))
    if not m:
        return None, None
    number, suffix = m.group(1), m.group(2)
    token = f"SA.{number}/{suffix}" if suffix else f"SA.{number}"
    return token, f"https://competition-cases.ec.europa.eu/cases/{token}"


# ---------------------------------------------------------------------------
# beneficiary_harvester: identity and normalisation
# ---------------------------------------------------------------------------


def normalize_for_hash(value: Any) -> str:
    """Case-folded NFKC text with compact whitespace; ``None``/NaN become ``""``."""
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    s = str(value).strip()
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s).casefold()
    return re.sub(r"\s+", " ", s)


def compute_record_hash(row: Mapping[str, Any], source_key: str) -> str:
    """Stable 32-hex identity over the profile hash fields plus the source key.

    The fields ``bundesland``, ``periode`` and ``fonds`` are part of the hash
    definition but are **not** present in parsed rows of the source
    application; they therefore contribute empty strings there (FS-W01).
    """
    parts: list[str] = [source_key]
    for name in profile()["hash_fields"]:
        parts.append(normalize_for_hash(row.get(name)))
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:32]


def normalize_company_name_simple(value: Any) -> str:
    """Search helper ``beneficiary_name_normalized`` (legal forms kept)."""
    if value is None:
        return ""
    s = str(value).translate(_ACCENT_TABLE).casefold()
    s = re.sub(r"[^\w\s\-]", " ", s, flags=re.UNICODE)
    return re.sub(r"\s+", " ", s).strip()


def stringify(value: Any) -> str | None:
    """Trimmed text or ``None``."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    s = str(value).strip()
    return s or None


def stringify_plz(value: Any) -> str | None:
    """Postcode as text; integral floats lose their ``.0`` (not a lost leading zero)."""
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value):
            return None
        if value.is_integer():
            return str(int(value))
    s = str(value).strip()
    return s or None


def coerce_float(value: Any) -> float | None:
    """Coordinate helper; decimal comma accepted, unparsable values ``None``."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        f = float(value)
        return None if math.isnan(f) else f
    try:
        return float(str(value).replace(",", ".").strip())
    except (ValueError, TypeError):
        return None


def detect_canonical_columns(
    headers: Sequence[str], explicit_mapping: Mapping[str, str] | None = None
) -> dict[str, str]:
    """``{alias: header}``; explicit mapping first, then the profile patterns (shortest match)."""
    data = profile()
    patterns = dict((role, list(p)) for role, p in data["column_patterns"])
    aliases = set(data["canonical_aliases"])
    mapping: dict[str, str] = {}
    if explicit_mapping:
        for alias, header in explicit_mapping.items():
            if alias not in aliases:
                continue
            if header and header in headers:
                mapping[alias] = header
    for alias in _ROLE_TO_ALIAS:
        if alias in mapping:
            continue
        for pattern in patterns.get(alias, []):
            candidates = [h for h in headers if re.search(pattern, h, re.IGNORECASE)]
            if candidates:
                mapping[alias] = min(candidates, key=len)
                break
    return mapping


def _cell(value: Any) -> Any:
    if isinstance(value, float) and math.isnan(value):
        return None
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:  # noqa: BLE001 - mirrors the source conversion
            return str(value)
    return value


def map_rows(
    headers: Sequence[Any],
    rows: Iterable[Sequence[Any]],
    field_mapping: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Beneficiary rows exactly like the loop of ``parse_xlsx_or_csv``.

    Each row keeps ``raw_row`` (every original cell), ``mapping`` and
    ``_row_number``; rows without a beneficiary name are returned with
    ``_skip_reason='no_name'`` instead of being dropped silently.
    """
    names = [str(c).strip() for c in headers]
    mapping = detect_canonical_columns(names, field_mapping)
    if "funded_at" not in mapping and "beginn" in mapping:
        mapping["funded_at"] = mapping["beginn"]
    result: list[dict[str, Any]] = []
    for index, values in enumerate(rows):
        raw_row: dict[str, Any] = {}
        for position, header in enumerate(names):
            raw_row[header] = _cell(values[position] if position < len(values) else None)
        canonical = {alias: raw_row.get(header) for alias, header in mapping.items()}
        name = (canonical.get("name") or "").strip() if canonical.get("name") else ""
        if not name:
            result.append(
                {
                    "_row_number": index + 1,
                    "_skip_reason": "no_name",
                    "raw_row": raw_row,
                    "mapping": mapping,
                }
            )
            continue
        result.append(
            {
                "_row_number": index + 1,
                "raw_row": raw_row,
                "mapping": mapping,
                "beneficiary_name": name,
                "project_name": stringify(canonical.get("projekt")),
                "project_aktenzeichen": stringify(canonical.get("aktenzeichen")),
                "project_description": stringify(canonical.get("beschreibung")),
                "cost_total_raw": stringify(canonical.get("kosten")),
                "cost_eu_funding_raw": stringify(canonical.get("kosten_eu")),
                "currency": stringify(canonical.get("currency")),
                "location": stringify(canonical.get("standort") or canonical.get("ort")),
                "landkreis": stringify(canonical.get("landkreis")),
                "plz": stringify_plz(canonical.get("plz")),
                "nuts_code": stringify(canonical.get("nuts")),
                "latitude": coerce_float(canonical.get("latitude")),
                "longitude": coerce_float(canonical.get("longitude")),
                "project_start_raw": stringify(canonical.get("beginn")),
                "project_end_raw": stringify(canonical.get("ende")),
                "funded_at_raw": stringify(canonical.get("funded_at")),
            }
        )
    return result


def _fund(value: Any) -> str:
    return str(value or "").strip().upper().replace("+", "").replace(" ", "")


def filter_by_fund(
    rows: list[dict[str, Any]], fund: str | None
) -> tuple[list[dict[str, Any]], int]:
    """Keep only the source's own fund when a file really mixes several funds.

    Returns ``(remaining rows, number removed)``. A uniform file, a missing fund
    column or a filter that would remove every row leaves the rows unchanged.
    """
    target = _fund(fund)
    if not target or not rows:
        return rows, 0
    columns = set(profile()["fund_columns"])
    column = None
    for candidate in rows[0].get("raw_row") or {}:
        if str(candidate).strip().lower() in columns:
            column = candidate
            break
    if column is None:
        return rows, 0
    values = {_fund((r.get("raw_row") or {}).get(column)) for r in rows}
    values.discard("")
    real = {v for v in values if len(v) <= 6}
    if len(real) < 2:
        return rows, 0
    kept = [r for r in rows if _fund((r.get("raw_row") or {}).get(column)) == target]
    if not kept:
        return rows, 0
    return kept, len(rows) - len(kept)


@dataclass(frozen=True)
class SnapshotContext:
    """Source context of a snapshot (``BeneficiaryHarvestParams`` without file/DB fields)."""

    source_key: str
    bundesland: str | None = None
    fonds: str | None = None
    periode: str | None = None
    country_code: str | None = None


def validate_rows(rows: Sequence[Mapping[str, Any]], context: SnapshotContext) -> list[str]:
    """Hard errors that must prevent replacing the previous inventory of the source."""
    limits = profile()["nameless"]
    errors: list[str] = []
    if not context.fonds or not context.periode or not context.country_code:
        errors.append("Quellenkontext Fonds, Förderperiode oder Land fehlt.")
    nameless = [r for r in rows if r.get("_skip_reason")]
    if nameless:
        share = len(nameless) / max(len(rows), 1)
        too_many = (
            share > limits["max_share"] and len(nameless) > limits["tolerance"]
        ) or share > limits["hard_limit"]
        if too_many:
            numbers = ", ".join(str(r.get("_row_number")) for r in nameless[:8])
            errors.append(
                f"{len(nameless)} von {len(rows)} Zeilen ohne Begünstigtennamen "
                f"({share:.0%}) — Kopfzeile oder Spaltenzuordnung prüfen. "
                f"Betroffen u.a.: {numbers}."
            )
    for row in rows:
        if row.get("_skip_reason"):
            continue
        nr = row.get("_row_number")
        total = parse_amount(row.get("cost_total_raw"))
        eu = parse_amount(row.get("cost_eu_funding_raw"))
        if total is not None and total < 0:
            errors.append(f"Zeile {nr}: Gesamtkosten dürfen nicht negativ sein.")
        if eu is not None and eu < 0:
            errors.append(f"Zeile {nr}: EU-Anteil darf nicht negativ sein.")
        if total is not None and eu is not None and eu > total:
            errors.append(f"Zeile {nr}: EU-Anteil ist größer als Gesamtkosten.")
        start, end = (
            parse_date(row.get("project_start_raw")),
            parse_date(row.get("project_end_raw")),
        )
        if start and end and start > end:
            errors.append(f"Zeile {nr}: Projektbeginn liegt nach Projektende.")
        lat, lon = row.get("latitude"), row.get("longitude")
        if lat is not None and not -90 <= float(lat) <= 90:
            errors.append(f"Zeile {nr}: Breitengrad außerhalb des gültigen Bereichs.")
        if lon is not None and not -180 <= float(lon) <= 180:
            errors.append(f"Zeile {nr}: Längengrad außerhalb des gültigen Bereichs.")
    return errors


def parse_file(
    content: bytes,
    file_name: str,
    *,
    sheet: str | int | None = None,
    header_row: int = 0,
    field_mapping: Mapping[str, str] | None = None,
    typing: str = "legacy",
    header_detection: str = "legacy",
) -> list[dict[str, Any]]:
    """``parse_xlsx_or_csv`` without pandas: read the table, then :func:`map_rows`.

    ``typing="legacy"`` reproduces the cell types of the source application;
    PDF lists (Saarland) are not read by this library.
    """
    from .tables import read_table

    table = read_table(
        content,
        file_name,
        sheet=sheet,
        header_row=header_row,
        typing="text" if typing == "text" else "legacy",
        header_detection="strict" if header_detection == "strict" else "legacy",
    )
    return map_rows(table.headers, table.rows, field_mapping)
