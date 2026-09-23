"""Publication pages as source snapshots (default: EU Weekly Oil Bulletin).

Characterized from regulierung ``external_apis/eu_oil_bulletin.py``: the
connector only fetches the publication page and records the SHA-256 of the
body; the bulletin itself is uploaded manually. No price is parsed — neither
there nor here. This adapter makes that snapshot explicit: one record per
page with digest, size, content type and the body (base64, bounded).
"""

from __future__ import annotations

import base64
import hashlib
from collections.abc import Mapping
from typing import Any

from auditcore_harvest import (
    AuthKind,
    Capabilities,
    ConfigError,
    FetchContext,
    HarvestRecord,
    PageResult,
    ParserError,
    SnapshotSemantics,
    Source,
    raise_for_status,
)

from .observation import RETRIEVAL_TIME, SNAPSHOT_SCHEMA

ADAPTER_VERSION = "1.0.0"
PROFILE_VERSION = "2026.09.1"
DEFAULT_MAX_BYTES = 5 * 1024 * 1024
TEXT_TYPES = ("text/html", "application/xhtml+xml", "text/plain")


class PageSnapshotAdapter:
    """``price.eu_oil_bulletin``: snapshot of the publication page (no price extraction)."""

    source = Source(
        source_id="price.eu_oil_bulletin",
        title="EU Weekly Oil Bulletin – Veröffentlichungsseite (Quellen-Snapshot)",
        family="price",
        adapter_version=ADAPTER_VERSION,
        profile_version=PROFILE_VERSION,
        data_format="text/html",
        auth=AuthKind.NONE,
        capabilities=Capabilities(
            pagination=False, incremental=False, full_snapshot=True, deletions=False
        ),
        snapshot_semantics=SnapshotSemantics.APPEND_ONLY,
    )

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """``url`` of the page and optional ``max_bytes``."""
        if not isinstance(config.get("url"), str) or not config["url"].startswith("http"):
            raise ConfigError("url der Veröffentlichungsseite fehlt.")
        limit = config.get("max_bytes", DEFAULT_MAX_BYTES)
        if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
            raise ConfigError("max_bytes muss positiv sein.")

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """Fetch the page; binary answers, NUL bytes and oversized bodies are parser errors."""
        url = str(context.config["url"])
        response = raise_for_status(context.transport.request("GET", url, timeout=context.timeout))
        limit = int(context.config.get("max_bytes", DEFAULT_MAX_BYTES))
        if len(response.body) > limit:
            raise ParserError("Seite überschreitet max_bytes.")
        content_type = (response.header("content-type") or "").split(";")[0].strip().lower()
        if content_type and content_type not in TEXT_TYPES or b"\x00" in response.body:
            raise ParserError("Antwort ist keine Textseite.")
        digest = hashlib.sha256(response.body).hexdigest()
        raw = {"url": url, "inhalt_b64": base64.b64encode(response.body).decode()}
        normalized = {
            "schema": SNAPSHOT_SCHEMA,
            "url": url,
            "sha256": digest,
            "bytes": len(response.body),
            "content_type": content_type or None,
            "zeitbezug": dict(RETRIEVAL_TIME),
            "preise_extrahiert": False,
        }
        record = HarvestRecord(
            source_id=self.source.source_id,
            record_id=f"{url}#{digest}",
            raw=raw,
            normalized=normalized,
            provenance=context.provenance(self.source, url, raw),
        )
        return PageResult((record,), None, complete=True)
