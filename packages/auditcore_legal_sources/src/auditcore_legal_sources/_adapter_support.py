"""Shared helpers of the harvest adapters: profile selection, records, issues and ``since``."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from auditcore_harvest import JSON, ConfigError, FetchContext, HarvestRecord, RecordIssue, Source

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


def _record(
    source: Source, context: FetchContext, document: LegalDocument, raw: JSON, locator: str
) -> HarvestRecord:
    return context.record(source, document.external_id, raw, document.to_dict(), locator)


def _issues(errors: Sequence[ParseError]) -> list[RecordIssue]:
    return [RecordIssue(error.location or "?", str(error)) for error in errors]


def _since(value: str | None) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError as exc:
        raise ConfigError(f"'since' ist kein ISO-Datum: {value!r}.") from exc
