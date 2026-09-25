"""Shared helpers of the harvest adapters: profile selection, JSON bodies, records and pages."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import date

from auditcore_harvest import (
    ConfigError,
    FetchContext,
    HarvestRecord,
    PageResult,
    PageStatus,
    ParserError,
    RecordIssue,
    Source,
)

from .errors import ParseError, ProfileError
from .model import LegalDocument
from .profile import SourceProfile, load_profile


def _profile(config: Mapping[str, object]) -> SourceProfile:
    spec = config.get("profile")
    if not isinstance(spec, Mapping) or not all(
        isinstance(spec.get(k), str) for k in ("id", "version")
    ):
        raise ConfigError("Konfiguration 'profile' mit 'id' und 'version' fehlt.")
    try:
        return load_profile(str(spec["id"]), str(spec["version"]))
    except ProfileError as exc:
        raise ConfigError(str(exc)) from exc


def _json(response_body: bytes, what: str) -> object:
    try:
        return json.loads(response_body)
    except ValueError as exc:
        raise ParserError(f"{what}: Antwort ist kein JSON.") from exc


def _record(
    source: Source, context: FetchContext, document: LegalDocument, raw: object, locator: str
) -> HarvestRecord:
    normalized = document.to_dict()
    return HarvestRecord(
        source_id=source.source_id,
        record_id=document.external_id,
        raw=raw,
        normalized=normalized,
        provenance=context.provenance(source, locator, raw),
    )


def _page(
    records: Sequence[HarvestRecord],
    issues: Sequence[RecordIssue],
    next_cursor: Mapping[str, object] | None,
    total: int | None = None,
) -> PageResult:
    return PageResult(
        records=tuple(records),
        next_cursor=dict(next_cursor) if next_cursor is not None else None,
        complete=next_cursor is None,
        status=PageStatus.PARTIAL if issues else PageStatus.OK,
        issues=tuple(issues),
        total_hint=total,
    )


def _issues(errors: Sequence[ParseError]) -> list[RecordIssue]:
    return [RecordIssue(error.location or "?", str(error)) for error in errors]


def _since(value: str | None) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError as exc:
        raise ConfigError(f"'since' ist kein ISO-Datum: {value!r}.") from exc
