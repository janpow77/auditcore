"""OpenSanctions ``targets.simple.csv``: the list format the source applications screen.

audit_designer, flowworkshop, flowinvoice (PEP) and the audit-portal import
all consume this format. Header observed live on 2026-09-23 (16 columns);
the portal serialiser writes the 12 columns its parser needs. Multi-valued
fields (aliases, countries, identifiers) are separated by ``;``.

Contract (deliberate differences to the originals, see ``docs/behavior-changes.md``):
the delivery must be UTF-8 (no silent Latin-1 fallback), the columns ``id``
and ``name`` must exist, rows without id or name are reported as issues and a
delivery without a single usable entry is a :class:`FormatError`, never an
empty list that could replace an inventory.
"""

from __future__ import annotations

import csv
import hashlib
import io
from collections.abc import Iterable

from .errors import FormatError
from .model import LIST_FIELDS, ListEntry, ParsedList, RowIssue

FORMAT = "opensanctions_targets_simple_csv"
#: Column header of ``targets.simple.csv`` as delivered on 2026-09-23.
SIMPLE_CSV_COLUMNS = (
    "id",
    "schema",
    "name",
    "aliases",
    "birth_date",
    "countries",
    "addresses",
    "identifiers",
    "sanctions",
    "phones",
    "emails",
    "program_ids",
    "dataset",
    "first_seen",
    "last_seen",
    "last_change",
)
#: The 12 columns written by the audit-portal serialiser (``SIMPLE_CSV_COLUMNS`` there).
PORTAL_COLUMNS = (
    "id",
    "schema",
    "name",
    "aliases",
    "birth_date",
    "countries",
    "addresses",
    "identifiers",
    "sanctions",
    "program_ids",
    "first_seen",
    "last_seen",
)
REQUIRED_COLUMNS = ("id", "name")


def split_multi(value: str | None) -> tuple[str, ...]:
    """``;``-separated multi-value field → stripped, non-empty parts in order."""
    if not value:
        return ()
    return tuple(part.strip() for part in value.split(";") if part.strip())


def parse_targets_simple_csv(data: bytes, *, list_key: str) -> ParsedList:
    """Parse one delivery of one list; see the module contract."""
    if not isinstance(data, bytes):
        raise TypeError("Die Lieferung ist als Bytes zu übergeben.")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise FormatError(
            f"Die Lieferung für '{list_key}' ist nicht UTF-8-kodiert (Byte {exc.start})."
        ) from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    try:
        header = reader.fieldnames
    except csv.Error as exc:
        raise FormatError(f"CSV-Kopfzeile nicht lesbar: {exc}") from exc
    if not header:
        raise FormatError(f"Die Lieferung für '{list_key}' ist leer.")
    columns = tuple(c.strip() for c in header)
    missing = [c for c in REQUIRED_COLUMNS if c not in columns]
    if missing:
        raise FormatError(
            f"Pflichtspalten fehlen: {', '.join(missing)} — erwartet wird das "
            "OpenSanctions-Format targets.simple.csv."
        )
    reader.fieldnames = list(columns)
    entries: list[ListEntry] = []
    issues: list[RowIssue] = []
    rows = 0
    try:
        for row in reader:
            rows += 1
            entry_id = (row.get("id") or "").strip()
            name = (row.get("name") or "").strip()
            if not entry_id or not name:
                reason = (
                    "Kennung und Name fehlen"
                    if not entry_id and not name
                    else ("Kennung fehlt" if not entry_id else "Name fehlt")
                )
                issues.append(RowIssue(rows, reason, entry_id or None))
                continue
            entries.append(
                ListEntry(
                    list_key=list_key,
                    entry_id=entry_id,
                    schema=(row.get("schema") or "").strip(),
                    name=name,
                    aliases=split_multi(row.get("aliases")),
                    **{f: (row.get(f) or "").strip() for f in LIST_FIELDS},
                )
            )
    except csv.Error as exc:
        raise FormatError(f"CSV-Zeile {rows + 1} nicht lesbar: {exc}") from exc
    if not entries:
        raise FormatError(
            f"Die Lieferung für '{list_key}' enthält keine verwertbaren Einträge "
            f"({rows} Zeilen gelesen)."
        )
    return ParsedList(
        list_key=list_key,
        format=FORMAT,
        entries=tuple(entries),
        issues=tuple(issues),
        rows_seen=rows,
        columns=columns,
        content_sha256=hashlib.sha256(data).hexdigest(),
    )


def serialize_targets_simple_csv(
    rows: Iterable[dict[str, str]], *, columns: tuple[str, ...] = PORTAL_COLUMNS
) -> bytes:
    """Deterministic CSV (``\\n``, UTF-8 without BOM, fixed columns); rows without id/name skipped.

    Byte-identical to the audit-portal serialiser for its 12 columns, so the
    same input yields the same SHA-256.
    """
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(columns), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        if not row.get("id") or not row.get("name"):
            continue
        writer.writerow({c: row.get(c, "") for c in columns})
    return buffer.getvalue().encode("utf-8")


def entry_to_row(entry: ListEntry) -> dict[str, str]:
    """Inverse of the parser for one entry (``aliases`` joined with ``;``)."""
    return {
        "id": entry.entry_id,
        "schema": entry.schema,
        "name": entry.name,
        "aliases": ";".join(entry.aliases),
        **{f: getattr(entry, f) for f in LIST_FIELDS},
    }
