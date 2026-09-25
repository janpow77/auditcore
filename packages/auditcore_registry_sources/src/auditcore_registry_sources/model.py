"""Data contracts: list entries, parsed deliveries and list snapshots.

Values a source does not state stay empty strings (list fields) or ``None``
(snapshot metadata); nothing is guessed. The displayed name is always the
spelling of the list; comparison forms are derived, never stored here.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ._types import JsonObject, JsonValue

LIST_FIELDS = (
    "birth_date",
    "countries",
    "addresses",
    "identifiers",
    "sanctions",
    "program_ids",
    "first_seen",
    "last_seen",
    "dataset",
)


@dataclass(frozen=True)
class SanctionsList:
    """One list of a list catalogue profile with its provider and data licence."""

    key: str
    source_key: str | None
    name: str
    issuer: str
    url: str
    format: str
    provider: str
    licence_claimed_in_source: str | None
    data_licence: Mapping[str, JsonValue]

    def to_dict(self) -> JsonObject:
        """JSON view."""
        return {
            "key": self.key,
            "source_key": self.source_key,
            "name": self.name,
            "issuer": self.issuer,
            "url": self.url,
            "format": self.format,
            "provider": self.provider,
            "licence_claimed_in_source": self.licence_claimed_in_source,
            "data_licence": dict(self.data_licence),
        }


@dataclass(frozen=True)
class ListEntry:
    """One listed person or organisation, spelled as the list spells it."""

    list_key: str
    entry_id: str
    schema: str
    name: str
    aliases: tuple[str, ...] = ()
    birth_date: str = ""
    countries: str = ""
    addresses: str = ""
    identifiers: str = ""
    sanctions: str = ""
    program_ids: str = ""
    first_seen: str = ""
    last_seen: str = ""
    dataset: str = ""

    def __post_init__(self) -> None:
        if not self.entry_id or not self.name:
            raise ValueError("Ein Listeneintrag braucht Kennung und Namen.")

    def to_dict(self) -> JsonObject:
        """JSON view."""
        return {
            "list_key": self.list_key,
            "entry_id": self.entry_id,
            "schema": self.schema,
            "name": self.name,
            "aliases": list(self.aliases),
            **{name: getattr(self, name) for name in LIST_FIELDS},
        }


@dataclass(frozen=True)
class RowIssue:
    """A row of a delivery that could not become an entry; never dropped silently."""

    row: int
    reason: str
    entry_id: str | None = None

    def to_dict(self) -> JsonObject:
        """JSON view."""
        return {"row": self.row, "reason": self.reason, "entry_id": self.entry_id}


@dataclass(frozen=True)
class ParsedList:
    """Result of parsing one delivery of one list."""

    list_key: str
    format: str
    entries: tuple[ListEntry, ...]
    issues: tuple[RowIssue, ...]
    rows_seen: int
    columns: tuple[str, ...]
    content_sha256: str
    as_of: str | None = None
    warnings: tuple[str, ...] = ()

    @property
    def complete(self) -> bool:
        """True if every row became an entry (a precondition for snapshot replacement)."""
        return not self.issues

    def to_dict(self) -> JsonObject:
        """JSON view (without the entries)."""
        return {
            "list_key": self.list_key,
            "format": self.format,
            "entries": len(self.entries),
            "issues": [i.to_dict() for i in self.issues],
            "rows_seen": self.rows_seen,
            "columns": list(self.columns),
            "content_sha256": self.content_sha256,
            "as_of": self.as_of,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class ListSnapshot:
    """The inventory of one list a screening runs against, with its state.

    ``as_of`` is the state of the list (Quellenstand), not the time of the
    query. A snapshot without entries is a list that was not searched.
    """

    list: SanctionsList
    entries: tuple[ListEntry, ...]
    as_of: str | None = None
    retrieved_at: str | None = None
    content_sha256: str | None = None
    note: str | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)
