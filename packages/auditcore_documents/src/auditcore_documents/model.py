"""Web-unabhängige Datenverträge des Dokumentvergleichs (unverändert aus dem Original)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any


@dataclass
class CompareItem:
    """Eine Vergleichseinheit aus einem Quelldokument."""

    source_id: str
    section: str = ""
    text: str = ""
    answer: str = ""
    comment: str = ""
    note: str = ""
    location: str = ""
    kind: str = "text"
    stable_id: str = ""
    order: int = 0


@dataclass
class CompareRow:
    """Eine Zeile der Vorschau und der abschließenden Synopse."""

    row_id: str
    status: str
    location: str
    old_text: str = ""
    new_text: str = ""
    old_answer: str = ""
    new_answer: str = ""
    old_comment: str = ""
    new_comment: str = ""
    old_note: str = ""
    new_note: str = ""
    reason: str = ""
    reason_source: str = ""
    reason_verified: bool | None = None
    reason_warning: str = ""
    selected: bool = True
    diff: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class ComparisonResult:
    """Vollständiges, JSON-serialisierbares Vergleichsergebnis."""

    version: str
    mode: str
    old_filename: str
    new_filename: str
    old_sha256: str
    new_sha256: str
    old_count: int
    new_count: int
    matched_count: int
    changed_count: int
    removed_count: int
    added_count: int
    rows: list[CompareRow]
    created_at: str
    # Umgestellte Textstellen: gleicher Wortlaut, andere Stelle.
    moved_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["rows"] = [asdict(row) for row in self.rows]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ComparisonResult:
        """Gegenstück zu :meth:`to_dict` (z. B. für gespeicherte Vorschauen).

        Unbekannte Schlüssel werden abgewiesen, damit ein fremdes oder
        verfälschtes JSON nicht still als Ergebnis gilt.
        """
        allowed = {f.name for f in fields(cls)}
        unknown = set(data) - allowed
        if unknown:
            raise ValueError(f"Unbekannte Ergebnisfelder: {', '.join(sorted(unknown))}")
        row_fields = {f.name for f in fields(CompareRow)}
        rows = []
        for row in data.get("rows", []):
            extra = set(row) - row_fields
            if extra:
                raise ValueError(f"Unbekannte Zeilenfelder: {', '.join(sorted(extra))}")
            rows.append(CompareRow(**row))
        return cls(**{**data, "rows": rows})
