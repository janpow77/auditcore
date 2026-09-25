"""audit-portal replays: VAT id extraction and the sanctions CSV import."""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Mapping
from typing import Any

from auditcore_entity_matching import load_profile as load_normalization
from auditcore_entity_matching import normalize

from ._legacy_shared import VERSION
from ._legacy_types import PortalRecord, PortalValidation

_VAT = re.compile(r"\b([A-Z]{2}[0-9A-Z]{8,12})\b")


def portal_vat_ids(value: str | None) -> list[str]:
    """``extract_vat_ids``: VAT id candidates of a free identifier field."""
    if not value:
        return []
    compact = re.sub(r"[\s\-\.]", "", value.upper())
    return list(dict.fromkeys(_VAT.findall(compact)))


def portal_record(row: Mapping[str, Any]) -> PortalRecord | None:
    """``audit_prep.sanctions.row_to_record``."""
    entry_id = (row.get("id") or "").strip()
    name = (row.get("name") or "").strip()
    if not entry_id or not name:
        return None

    def multi(value: str | None) -> list[str]:
        """``;``-separated values."""
        return [p.strip() for p in str(value).split(";") if p.strip()] if value else []

    name_profile = load_normalization("audit_portal.name", VERSION)
    folded = load_normalization("audit_portal.name_folded", VERSION)
    aliases = multi(row.get("aliases"))
    identifiers = (row.get("identifiers") or "").strip()
    return {
        "entry_id": entry_id,
        "schema": (row.get("schema") or "").strip(),
        "name": name,
        "aliases": aliases,
        "birth_date": (row.get("birth_date") or "").strip(),
        "countries": multi(row.get("countries")),
        "addresses": (row.get("addresses") or "").strip(),
        "identifiers": identifiers,
        "sanctions": (row.get("sanctions") or "").strip(),
        "program_ids": (row.get("program_ids") or "").strip(),
        "first_seen": (row.get("first_seen") or "").strip(),
        "last_seen": (row.get("last_seen") or "").strip(),
        "name_norm": normalize(name, name_profile),
        "name_folded": normalize(name, folded),
        "alias_folded": [normalize(a, folded) for a in aliases],
        "vat_ids": portal_vat_ids(identifiers),
    }


def portal_parse_sanctions_csv(
    data: bytes,
) -> tuple[list[PortalRecord], list[str], PortalValidation]:
    """``audit_prep.sanctions.parse_sanctions_csv`` (with its Latin-1 fallback)."""
    validation: PortalValidation = {"errors": [], "warnings": []}
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("latin-1")
        validation["warnings"].append("Datei nicht UTF-8-kodiert — Latin-1-Fallback verwendet.")
    reader = csv.DictReader(io.StringIO(text))
    columns = [c.strip() for c in (reader.fieldnames or [])]
    missing = [c for c in ("id", "name") if c not in columns]
    if missing:
        validation["errors"].append(
            f"Pflichtspalten fehlen: {', '.join(missing)} — erwartet wird "
            "das OpenSanctions-Format targets.simple.csv."
        )
        return [], columns, validation
    records, skipped = [], 0
    for row in reader:
        record = portal_record(row)
        if record is None:
            skipped += 1
            continue
        records.append(record)
    if skipped:
        validation["warnings"].append(f"{skipped} Zeile(n) ohne id/name übersprungen.")
    if not records:
        validation["errors"].append("Die Datei enthält keine verwertbaren Sanktionseinträge.")
    return records, columns, validation
