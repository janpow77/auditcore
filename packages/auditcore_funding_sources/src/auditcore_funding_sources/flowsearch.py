"""Source profile ``flowsearch.beneficiaries``: a separate, not harmonised variant.

Behavior of ``janpow77/flowsearch@10cb2a3``
(``backend/app/services/eu_beneficiary_harvester_v2.py``). It differs from the
flowworkshop profile on purpose and stays separate: amounts are ``float`` and
a missing or unparsable amount becomes ``0.0`` (FS-S01), identities are MD5
over name, title and start date (FS-S02), column mappings are explicit per
source. The functions reproduce recorded outputs exactly; :func:`record_values`
additionally reports where the variant defaulted a value.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
import zipfile
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

from .errors import OptionalDependencyError, SourceFormatError

PROFILE_ID = "flowsearch.beneficiaries"
NUTS1 = {
    "Baden-Württemberg": "DE1",
    "Bayern": "DE2",
    "Berlin": "DE3",
    "Brandenburg": "DE4",
    "Bremen": "DE5",
    "Hamburg": "DE6",
    "Hessen": "DE7",
    "Mecklenburg-Vorpommern": "DE8",
    "Niedersachsen": "DE9",
    "Nordrhein-Westfalen": "DEA",
    "Rheinland-Pfalz": "DEB",
    "Saarland": "DEC",
    "Sachsen": "DED",
    "Sachsen-Anhalt": "DEE",
    "Schleswig-Holstein": "DEF",
    "Thüringen": "DEG",
}
MAX_ARCHIVE_MEMBER_BYTES = 64 * 1024 * 1024


def parse_amount(value: object) -> float:
    """Float amount; missing or unparsable values become ``0.0`` (source behavior)."""
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("€", "").replace("EUR", "").strip()
    has_comma, has_dot = "," in text, "." in text
    if has_comma and has_dot:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif has_comma:
        text = text.replace(",", ".")
    try:
        return float(text)
    except (ValueError, TypeError):
        return 0.0


def parse_date(value: object) -> date | None:
    """Excel dates, ``DD.MM.YYYY``, ``YYYY-MM-DD``, ``DD/MM/YYYY``."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def parse_location(value: object) -> tuple[str | None, str | None]:
    """``(city, postal code)`` from ``"12345 City"``, ``"City, 12345"`` or either alone."""
    if not value:
        return None, None
    text = str(value).strip()
    match = re.match(r"^(\d{5})\s+(.+)$", text)
    if match:
        return match.group(2).strip(), match.group(1)
    match = re.match(r"^(.+?),\s*(\d{5})$", text)
    if match:
        return match.group(1).strip(), match.group(2)
    if re.match(r"^\d{5}$", text):
        return None, text
    return text, None


def normalize_name(name: str) -> str:
    """Search form of the variant (a few German legal forms removed)."""
    name = re.sub(r"\b(GmbH|AG|KG|OHG|GbR|e\.V\.|mbH|gGmbH)\b", "", name, flags=re.IGNORECASE)
    name = re.sub(r"[^\w\s]", " ", name)
    return " ".join(name.split()).lower().strip()


def truncate(value: str | None, max_length: int) -> str | None:
    """Cut text to ``max_length`` characters."""
    if value is None:
        return None
    return value if len(value) <= max_length else value[:max_length]


def extract_mapped_field(
    record: Mapping[str, Any],
    columns: Mapping[str, str],
    field_name: str,
    fallback: Mapping[str, Any] | None = None,
) -> str | None:
    """Exact column mapping, then the fuzzy names of the ``_fallback`` mapping."""
    column = columns.get(field_name)
    if column and column in record:
        value = record[column]
        if value is not None and value != "":
            return str(value).strip()
    if fallback is not None:
        for keyword in (fallback.get("fuzzy_column_names", {}) or {}).get(field_name, []):
            for key, value in record.items():
                if keyword.lower() in key.lower() and value:
                    return str(value).strip()
    return None


def extract_from_zip(content: bytes, *, max_member_bytes: int = MAX_ARCHIVE_MEMBER_BYTES) -> bytes:
    """First table file of a ZIP archive.

    The source read the member without a size check; this version refuses
    members larger than ``max_member_bytes`` (FS-S03).
    """
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise SourceFormatError("Kein gültiges ZIP-Archiv.") from exc
    with archive:
        names = [n for n in archive.namelist() if n.lower().endswith((".xlsx", ".xls", ".csv"))]
        if not names:
            raise ValueError("Keine Tabellendatei in ZIP gefunden")
        info = archive.getinfo(names[0])
        if info.file_size > max_member_bytes:
            raise SourceFormatError(
                "Die Tabellendatei im Archiv überschreitet die zulässige Größe."
            )
        return archive.read(names[0])


def parse_csv(content: bytes, mapping: Mapping[str, Any] | None) -> list[dict[str, str]]:
    """``DictReader`` rows after ``skip_rows`` lines, delimiter from the mapping."""
    text = content.decode("utf-8", errors="replace")
    delimiter = mapping.get("delimiter", ";") if mapping else ";"
    skip = mapping.get("skip_rows", 0) if mapping else 0
    lines = text.split("\n")
    if skip > 0:
        lines = lines[skip:]
    return list(csv.DictReader(io.StringIO("\n".join(lines)), delimiter=delimiter))


def parse_excel(content: bytes, mapping: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    """Active sheet; header at ``header_row`` (1-based), empty rows dropped."""
    try:
        import openpyxl
    except ImportError as exc:  # pragma: no cover
        raise OptionalDependencyError(
            "XLSX-Dateien benötigen das Extra auditcore_funding_sources[xlsx] (openpyxl)."
        ) from exc
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    if ws is None:
        wb.close()
        raise ValueError("Die XLSX-Datei enthält kein aktives Tabellenblatt.")
    skip = mapping.get("skip_rows", 0) if mapping else 0
    header_row = mapping.get("header_row", skip + 1) if mapping else 1
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows or len(rows) <= header_row:
        return []
    headers = rows[header_row - 1]
    records = []
    for row in rows[header_row:]:
        record: dict[str, Any] = {}
        for i, value in enumerate(row):
            if i < len(headers) and headers[i]:
                record[str(headers[i]).replace("\n", " ").strip()] = value
        if any(record.values()):
            records.append(record)
    return records


def read_items(
    content: bytes, url: str, source: Mapping[str, Any], mapping: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Records of one downloaded file: unzip, then CSV or the active XLSX sheet.

    CSV is chosen by the URL or the source note ``"csv statt xlsx"``.
    """
    if url.lower().endswith(".zip"):
        content = extract_from_zip(content)
    if url.lower().endswith(".csv") or str(source.get("notes", "")).lower() == "csv statt xlsx":
        return [dict(r) for r in parse_csv(content, mapping)]
    return parse_excel(content, mapping)


def project_id(
    source_key: str, beneficiary_name: str, project_title: str, start_date: date | None
) -> str:
    """Identity of the variant: MD5 over key, name, title and start date (16 hex)."""
    base = f"{source_key}_{beneficiary_name}_{project_title}_{start_date}"
    return hashlib.md5(base.encode(), usedforsecurity=False).hexdigest()[:16]


def record_values(
    record: Mapping[str, Any],
    source: Mapping[str, Any],
    mappings: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Field values of ``_import_record`` for a new record, without database access.

    Returns ``None`` where the source skipped the row. ``defaulted`` lists
    amounts that the variant set to ``0.0`` because the source value was
    missing or not a number, so a consumer can see them.
    """
    mapping = mappings.get(source["source_key"], mappings.get("_fallback"))
    if not mapping:
        return None
    columns = mapping.get("columns", {})
    fallback = mappings.get("_fallback") if "_fallback" in mappings else None

    def field(name: str) -> str | None:
        """Mapped field of this record."""
        return extract_mapped_field(record, columns, name, fallback)

    name = field("beneficiary_name")
    if "firstname" in columns.get("beneficiary_name", "").lower():
        first = field("beneficiary_firstname")
        if first:
            name = f"{first} {name}".strip()
    if not name:
        return None
    name = truncate(name, 500) or ""
    title = field("project_name") or ""
    summary = field("project_purpose") or ""
    start = parse_date(field("start_date"))
    end = parse_date(field("end_date"))
    raw_total, raw_eu = field("total_cost"), field("eu_contribution")
    total = parse_amount(raw_total)
    eu = parse_amount(raw_eu)
    national = total - eu if total > eu else 0.0
    city, postal = parse_location(field("location"))
    defaulted = [
        label
        for label, raw in (("total_cost", raw_total), ("eu_contribution", raw_eu))
        if parse_amount(raw) == 0.0 and (raw in (None, "") or not re.search(r"\d", str(raw)))
    ]
    return {
        "project_id": project_id(source["source_key"], name, title, start),
        "beneficiary_name": name,
        "beneficiary_name_normalized": normalize_name(name),
        "fund_type": source["fonds"],
        "nuts0": "DE",
        "nuts1": NUTS1.get(source["bundesland"]),
        "eu_cofinancing": eu,
        "national_cofinancing": national,
        "total_amount": total,
        "total_eligible_expenditure": total,
        "project_title": title,
        "project_summary": summary,
        "start_date": start,
        "end_date": end,
        "city": city,
        "postal_code": postal,
        "data_source": f"{source['bundesland']} {source['fonds']}",
        "data_source_url": source.get("portal", ""),
        "programming_period": source.get("periode", "2021-2027"),
        "defaulted": defaulted,
    }
