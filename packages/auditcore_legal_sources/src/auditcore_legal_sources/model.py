"""Normalized legal/audit source document with provenance.

The flow contract (records, results, cursors, sinks) belongs to
``auditcore_harvest``; this module only defines the domain content of one
document of this source family.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime

from auditcore_harvest import JSON

ADAPTER_VERSION = "0.1.0"


@dataclass(frozen=True)
class LegalDocument:
    """A parliamentary, legal or audit publication in normalized form."""

    source_id: str
    external_id: str
    title: str
    publication_date: date | None
    date_precision: str | None
    raw_date: str | None
    source_url: str | None
    document_url: str | None = None
    document_type: str | None = None
    language: str = "de"
    content: str | None = None
    abstract: str | None = None
    classification: Mapping[str, JSON] = field(default_factory=dict)
    metadata: Mapping[str, JSON] = field(default_factory=dict)
    profile: Mapping[str, str] = field(default_factory=dict)
    adapter: str = ""
    adapter_version: str = ADAPTER_VERSION

    @property
    def identity(self) -> str:
        """Stable source-scoped identity used for deduplication."""
        return f"{self.source_id}:{self.external_id}"

    @property
    def content_hash(self) -> str:
        """SHA-256 of content, else abstract, else title (source-compatible definition)."""
        text = self.content or self.abstract or self.title
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, JSON]:
        """JSON-compatible representation including hash and identity."""
        return {
            "source_id": self.source_id,
            "external_id": self.external_id,
            "identity": self.identity,
            "title": self.title,
            "publication_date": self.publication_date.isoformat()
            if self.publication_date
            else None,
            "date_precision": self.date_precision,
            "raw_date": self.raw_date,
            "source_url": self.source_url,
            "document_url": self.document_url,
            "document_type": self.document_type,
            "language": self.language,
            "content": self.content,
            "abstract": self.abstract,
            "classification": dict(self.classification),
            "metadata": dict(self.metadata),
            "profile": dict(self.profile),
            "adapter": self.adapter,
            "adapter_version": self.adapter_version,
            "content_hash": self.content_hash,
        }


def as_date(value: date | datetime) -> date:
    """Calendar date of a date or datetime."""
    return value.date() if isinstance(value, datetime) else value
