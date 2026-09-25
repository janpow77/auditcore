"""Frameworkfreier Dienst hinter dem REST-Vertrag (nur Standardbibliothek).

Der Dienst vergleicht hochgeladene Fassungen, verwaltet gespeicherte
Vergleiche eines Eigentümers, übernimmt Auswahl und Begründungen je Zeile
und erzeugt Ausgaben. Starlette- und FastAPI-Adapter rufen nur diesen
Dienst auf; Anwendungen können ihn ebenso aus eigenen Routen nutzen.
"""

from __future__ import annotations

import copy
import tempfile
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PurePath

from auditcore_documents.compare import ReadContext, compare_files
from auditcore_documents.errors import CompareError, DependencyError, LimitExceededError
from auditcore_documents.limits import DEFAULT_LIMITS, ReadLimits
from auditcore_documents.model import ComparisonResult
from auditcore_documents.profiles import PROFILES, RECOMMENDED, CompareProfile
from auditcore_documents.reading import ALLOWED_EXTENSIONS
from auditcore_documents.web.export import (
    EXPORT_FORMATS,
    ExportFile,
    ExportSettings,
    export_comparison,
)
from auditcore_documents.web.options import (
    RequestError,
    parse_compare_fields,
    parse_row_updates,
)
from auditcore_documents.web.store import (
    ComparisonStore,
    InMemoryComparisonStore,
    StoredComparison,
)

MAX_FILENAME = 200


@dataclass(frozen=True)
class Upload:
    """Eine hochgeladene Datei im Speicher."""

    filename: str
    content: bytes


@dataclass(frozen=True)
class ServiceSettings:
    """Grenzen und Vorgaben; Anwendungen verschärfen sie ausdrücklich."""

    #: Größe je hochgeladener Datei (ecohesion: 10 MiB, Designer: 100 MiB).
    max_upload_bytes: int = 20 * 1024 * 1024
    default_profile: CompareProfile = RECOMMENDED
    allowed_profiles: frozenset[str] = frozenset(PROFILES)
    read_limits: ReadLimits = DEFAULT_LIMITS
    export: ExportSettings = field(default_factory=ExportSettings)

    def __post_init__(self) -> None:
        if type(self.max_upload_bytes) is not int or self.max_upload_bytes < 1:
            raise ValueError("max_upload_bytes muss eine positive ganze Zahl sein")
        if self.default_profile.profile_id not in self.allowed_profiles:
            raise ValueError("Das Standardprofil muss zu den erlaubten Profilen gehören")


def error_status(exc: Exception) -> int:
    """HTTP-Status für fachliche Fehler der Bibliothek."""
    if isinstance(exc, RequestError):
        return exc.status
    if isinstance(exc, LimitExceededError):
        return 413
    if isinstance(exc, DependencyError):
        return 501
    return 422


def safe_filename(name: str) -> str:
    """Nur den letzten Namensteil ohne Steuerzeichen behalten; Endung prüfen."""
    base = PurePath(name.replace("\\", "/")).name
    cleaned = "".join(ch for ch in base if ch.isprintable() and ch not in '/\\:*?"<>|').strip()
    if not cleaned or cleaned.startswith("."):
        raise RequestError(422, "Der Dateiname ist ungültig.")
    if PurePath(cleaned).suffix.casefold() not in ALLOWED_EXTENSIONS:
        raise RequestError(415, "Bitte eine DOCX-, DOCM- oder PDF-Datei auswählen.")
    if len(cleaned) > MAX_FILENAME:
        suffix = PurePath(cleaned).suffix
        cleaned = cleaned[: MAX_FILENAME - len(suffix)] + suffix
    return cleaned


class SynopsisService:
    """Anwendungsfälle der Synopse-Oberfläche."""

    def __init__(
        self,
        store: ComparisonStore | None = None,
        *,
        settings: ServiceSettings | None = None,
        context: ReadContext | None = None,
        now: Callable[[], datetime] | None = None,
        new_id: Callable[[], str] | None = None,
    ) -> None:
        self.store: ComparisonStore = store if store is not None else InMemoryComparisonStore()
        self.settings = settings or ServiceSettings()
        self._context = context or ReadContext(limits=self.settings.read_limits)
        self._now = now or (lambda: datetime.now(UTC))
        self._new_id = new_id or (lambda: uuid.uuid4().hex)

    def profiles(self) -> list[dict[str, object]]:
        """Erlaubte Profile mit Kennung, Version, Fingerabdruck und Status."""
        default = self.settings.default_profile.profile_id
        return [
            {**profile.identity(), "status": profile.status, "default": pid == default}
            for pid, profile in PROFILES.items()
            if pid in self.settings.allowed_profiles
        ]

    def _check_upload(self, upload: Upload, label: str) -> str:
        if len(upload.content) > self.settings.max_upload_bytes:
            limit = self.settings.max_upload_bytes // (1024 * 1024) or 1
            raise RequestError(413, f"{label}: Eine Datei darf höchstens {limit} MiB groß sein.")
        if not upload.content:
            raise RequestError(422, f"{label}: Die hochgeladene Datei ist leer.")
        return safe_filename(upload.filename)

    def compare(
        self, old: Upload, new: Upload, fields: Mapping[str, str]
    ) -> tuple[str, ComparisonResult]:
        """Vergleich ohne Ablage; blockiert (Adapter rufen ihn im Thread auf)."""
        old_name = self._check_upload(old, "Bisherige Fassung")
        new_name = self._check_upload(new, "Neue Fassung")
        request = parse_compare_fields(
            fields,
            default_profile=self.settings.default_profile,
            allowed_profiles=self.settings.allowed_profiles,
            fallback_title=f"Vergleich von {old_name} mit {new_name}",
        )
        with tempfile.TemporaryDirectory(prefix="auditcore-synopsis-") as work:
            old_path = Path(work, "old", old_name)
            new_path = Path(work, "new", new_name)
            for path, upload in ((old_path, old), (new_path, new)):
                path.parent.mkdir(mode=0o700)
                path.write_bytes(upload.content)
            result = compare_files(
                old_path,
                new_path,
                profile=request.profile,
                options=request.options,
                context=self._context,
            )
        return request.title, result

    def create(
        self, owner: str, old: Upload, new: Upload, fields: Mapping[str, str]
    ) -> StoredComparison:
        title, result = self.compare(old, new, fields)
        return self._store(owner, title, result)

    def import_result(self, owner: str, payload: object) -> StoredComparison:
        """Ein vorhandenes Ergebnis (z. B. aus ``--json`` der CLI) übernehmen."""
        if not isinstance(payload, dict) or not isinstance(payload.get("result"), dict):
            raise RequestError(422, 'Erwartet wird {"title"?, "result": {…}}.')
        unknown = sorted(set(payload) - {"title", "result"})
        if unknown:
            raise RequestError(422, f"Unbekannte Felder: {', '.join(unknown)}")
        try:
            result = ComparisonResult.from_dict(payload["result"])
        except (TypeError, ValueError) as exc:
            raise RequestError(422, f"Kein gültiges Vergleichsergebnis: {exc}") from None
        title = (
            payload.get("title") or f"Vergleich von {result.old_filename} mit {result.new_filename}"
        )
        if not isinstance(title, str) or len(title) > 255:
            raise RequestError(422, "Der Titel darf höchstens 255 Zeichen lang sein.")
        return self._store(owner, title, result)

    def _store(self, owner: str, title: str, result: ComparisonResult) -> StoredComparison:
        item = StoredComparison(
            comparison_id=self._new_id(),
            owner=owner,
            title=title,
            created_at=self._now().isoformat(),
            result=result,
        )
        self.store.add(item)
        return item

    def list(self, owner: str) -> list[dict[str, object]]:
        return [item.summary() for item in self.store.list(owner)]

    def get(self, owner: str, comparison_id: str) -> StoredComparison:
        item = self.store.get(owner, comparison_id)
        if item is None:
            raise RequestError(404, "Vergleich nicht gefunden.")
        return item

    def update_rows(self, owner: str, comparison_id: str, payload: object) -> StoredComparison:
        """Auswahl und Grund je Zeile übernehmen (Vorschau des Designers)."""
        item = self.get(owner, comparison_id)
        updates = parse_row_updates(payload)
        result = copy.deepcopy(item.result)
        rows = {row.row_id: row for row in result.rows}
        for update in updates:
            row = rows.get(update.row_id)
            if row is None:
                raise RequestError(422, f"Unbekannte Zeile: {update.row_id}")
            if update.selected is not None:
                row.selected = update.selected
            if update.reason is not None:
                row.reason = update.reason
        changed = StoredComparison(item.comparison_id, owner, item.title, item.created_at, result)
        self.store.replace(changed)
        return changed

    def delete(self, owner: str, comparison_id: str) -> None:
        if not self.store.delete(owner, comparison_id):
            raise RequestError(404, "Vergleich nicht gefunden.")

    def export(self, owner: str, comparison_id: str, fmt: str) -> ExportFile:
        if fmt not in EXPORT_FORMATS:
            raise RequestError(422, f"Ausgabeformat erlaubt nur: {', '.join(EXPORT_FORMATS)}.")
        item = self.get(owner, comparison_id)
        return export_comparison(
            item.result, title=item.title, fmt=fmt, settings=self.settings.export
        )


__all__ = [
    "CompareError",
    "RequestError",
    "ServiceSettings",
    "SynopsisService",
    "Upload",
    "error_status",
    "safe_filename",
]
