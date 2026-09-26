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
from typing import Any

from .profiles import load_profile
from .workshop_state_aid import PROFILE_ID as PROFILE_ID
from .workshop_state_aid import detect_sa_reference as detect_sa_reference
from .workshop_state_aid import normalize_company_name as normalize_company_name
from .workshop_state_aid import parse_amount as parse_amount
from .workshop_state_aid import parse_date as parse_date
from .workshop_state_aid import strip_accents as strip_accents

MODES = ("smart", "full-refresh", "force", "snapshot")

_ACCENT_TABLE = str.maketrans(
    {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "ae", "Ö": "oe", "Ü": "ue"}
)
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
# beneficiary_harvester: identity and normalisation
# ---------------------------------------------------------------------------


def normalize_for_hash(value: object) -> str:
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


def compute_record_hash(row: Mapping[str, object], source_key: str) -> str:
    """Stable 32-hex identity over the profile hash fields plus the source key.

    The fields ``bundesland``, ``periode`` and ``fonds`` are part of the hash
    definition but are **not** present in parsed rows of the source
    application; they therefore contribute empty strings there (FS-W01).
    """
    parts: list[str] = [source_key]
    for name in profile()["hash_fields"]:
        parts.append(normalize_for_hash(row.get(name)))
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:32]


def normalize_company_name_simple(value: object) -> str:
    """Search helper ``beneficiary_name_normalized`` (legal forms kept)."""
    if value is None:
        return ""
    s = str(value).translate(_ACCENT_TABLE).casefold()
    s = re.sub(r"[^\w\s\-]", " ", s, flags=re.UNICODE)
    return re.sub(r"\s+", " ", s).strip()


def stringify(value: object) -> str | None:
    """Trimmed text or ``None``."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    s = str(value).strip()
    return s or None


def stringify_plz(value: object) -> str | None:
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


def coerce_float(value: object) -> float | None:
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


def _cell(value: object) -> object:
    if isinstance(value, float) and math.isnan(value):
        return None
    isoformat = getattr(value, "isoformat", None)
    if isoformat is not None:
        try:
            return isoformat()
        except Exception:  # noqa: BLE001 - mirrors the source conversion
            return str(value)
    return value


def map_rows(
    headers: Sequence[object],
    rows: Iterable[Sequence[object]],
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


#: Row fields copied unchanged into the harvest record (source column order).
HARVEST_TEXT_FIELDS = (
    "beneficiary_name",
    "project_name",
    "project_aktenzeichen",
    "project_description",
    "cost_total_raw",
    "cost_eu_funding_raw",
    "currency",
    "location",
    "landkreis",
    "plz",
    "nuts_code",
    "latitude",
    "longitude",
    "project_start_raw",
    "project_end_raw",
    "funded_at_raw",
)


def harvest_values(row: Mapping[str, Any]) -> dict[str, object]:
    """Normalised values of one named row: text fields plus parsed amounts and dates."""
    values: dict[str, object] = {key: row.get(key) for key in HARVEST_TEXT_FIELDS}
    values.update(
        {
            "beneficiary_name_normalized": normalize_company_name_simple(row["beneficiary_name"]),
            "cost_total": parse_amount(row.get("cost_total_raw")),
            "cost_eu_funding": parse_amount(row.get("cost_eu_funding_raw")),
            "project_start": parse_date(row.get("project_start_raw")),
            "project_end": parse_date(row.get("project_end_raw")),
            "funded_at": parse_date(row.get("funded_at_raw")),
            "source_row_number": row.get("_row_number"),
        }
    )
    return values


def _fund(value: object) -> str:
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
    errors: list[str] = []
    if not context.fonds or not context.periode or not context.country_code:
        errors.append("Quellenkontext Fonds, Förderperiode oder Land fehlt.")
    errors.extend(_nameless_errors(rows, profile()["nameless"]))
    for row in rows:
        if not row.get("_skip_reason"):
            errors.extend(_row_errors(row))
    return errors


def _nameless_errors(rows: Sequence[Mapping[str, Any]], limits: Mapping[str, Any]) -> list[str]:
    """Too many rows without beneficiary name point to a wrong header or mapping."""
    nameless = [r for r in rows if r.get("_skip_reason")]
    if not nameless:
        return []
    share = len(nameless) / max(len(rows), 1)
    too_many = (
        share > limits["max_share"] and len(nameless) > limits["tolerance"]
    ) or share > limits["hard_limit"]
    if not too_many:
        return []
    numbers = ", ".join(str(r.get("_row_number")) for r in nameless[:8])
    return [
        f"{len(nameless)} von {len(rows)} Zeilen ohne Begünstigtennamen "
        f"({share:.0%}) — Kopfzeile oder Spaltenzuordnung prüfen. "
        f"Betroffen u.a.: {numbers}."
    ]


def _row_errors(row: Mapping[str, Any]) -> list[str]:
    """Amount, period and coordinate errors of one named row, in source order."""
    nr = row.get("_row_number")
    total = parse_amount(row.get("cost_total_raw"))
    eu = parse_amount(row.get("cost_eu_funding_raw"))
    start = parse_date(row.get("project_start_raw"))
    end = parse_date(row.get("project_end_raw"))
    lat, lon = row.get("latitude"), row.get("longitude")
    checks = (
        (total is not None and total < 0, "Gesamtkosten dürfen nicht negativ sein."),
        (eu is not None and eu < 0, "EU-Anteil darf nicht negativ sein."),
        (
            total is not None and eu is not None and eu > total,
            "EU-Anteil ist größer als Gesamtkosten.",
        ),
        (bool(start and end and start > end), "Projektbeginn liegt nach Projektende."),
        (
            lat is not None and not -90 <= float(lat) <= 90,
            "Breitengrad außerhalb des gültigen Bereichs.",
        ),
        (
            lon is not None and not -180 <= float(lon) <= 180,
            "Längengrad außerhalb des gültigen Bereichs.",
        ),
    )
    return [f"Zeile {nr}: {message}" for failed, message in checks if failed]


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
