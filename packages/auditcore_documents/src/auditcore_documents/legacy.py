"""Kompatibilitätsfassade für die Umstellung von audit_designer.

``DocumentCompareService`` hat dieselben Namen, Signaturen, Konstanten und
Fehlertexte wie ``app.modules.document_compare.service`` am Quellstand
030a71e0 und verwendet das Profil ``LEGACY``. Unterschiede sind in
``docs/behavior-changes.md`` begründet (DC-C01 bis DC-C06). Die KI-Anbindung
ist ein Port: Die Anwendung setzt ``DocumentCompareService.reason_provider``.
"""

from __future__ import annotations

import getpass
import os
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any, ClassVar

from auditcore_documents.compare import CompareOptions, ReadContext, compare_files
from auditcore_documents.errors import CompareError
from auditcore_documents.model import CompareItem, CompareRow, ComparisonResult
from auditcore_documents.pdftext import OcrCallback
from auditcore_documents.profiles import LEGACY, CompareProfile
from auditcore_documents.reading import ALLOWED_EXTENSIONS
from auditcore_documents.reading import detect_mode as _detect_mode
from auditcore_documents.reading import read_document as _read_document
from auditcore_documents.reasons import ReasonProvider, apply_reasons_cli, generate_reason
from auditcore_documents.render_docx import render_docx as _render_docx
from auditcore_documents.settings import load_settings, merge_settings, save_settings

__all__ = [
    "CompareError",
    "CompareItem",
    "CompareRow",
    "ComparisonResult",
    "DocumentCompareService",
    "audit_designer_config_path",
    "compare_documents",
    "read_document",
]


class DocumentCompareService:
    """Fassade mit dem Vertrag des Originals (API, Celery, CLI, Jupyter)."""

    VERSION = "1.1.0"
    ALLOWED_EXTENSIONS = set(ALLOWED_EXTENSIONS)
    profile: ClassVar[CompareProfile] = LEGACY
    #: Von der Anwendung gesetzter KI-Port; ohne ihn keine Begründungsvorschläge.
    reason_provider: ClassVar[ReasonProvider | None] = None

    @classmethod
    def detect_mode(cls, path: Path) -> str:
        return _detect_mode(path)

    @classmethod
    def read(
        cls, path: Path, mode: str = "auto", *, ocr_callback: OcrCallback | None = None
    ) -> tuple[str, list[CompareItem]]:
        return _read_document(path, mode, ocr_callback=ocr_callback)

    @classmethod
    def compare(
        cls,
        old: Path,
        new: Path,
        *,
        mode: str = "auto",
        threshold: int = 85,
        include_answers: bool = True,
        include_notes: bool = True,
        include_editorial: bool = False,
        highlight_words: bool = True,
        output_sections: list[str] | None = None,
        comparison_type: str = "standard",
        ocr_callback: OcrCallback | None = None,
    ) -> ComparisonResult:
        return compare_files(
            old,
            new,
            profile=cls.profile,
            options=CompareOptions(
                mode=mode,
                threshold=threshold,
                include_answers=include_answers,
                include_notes=include_notes,
                include_editorial=include_editorial,
                highlight_words=highlight_words,
                output_sections=output_sections,
                comparison_type=comparison_type,
            ),
            context=ReadContext(ocr_callback=ocr_callback),
        )

    @classmethod
    def generate_reason(
        cls, old_text: str, new_text: str, model: str | None = None
    ) -> tuple[str, dict[str, Any]]:
        provider = cls.reason_provider
        if provider is None:
            raise CompareError(
                "Kein Begründungsdienst konfiguriert (DocumentCompareService.reason_provider)."
            )
        return generate_reason(old_text, new_text, model, provider=provider)

    @classmethod
    def render_docx(
        cls,
        result: ComparisonResult,
        output: Path,
        *,
        title: str | None = None,
        user: str = "",
        header: str | None = None,
        profile: str = "memo",
        layout: dict[str, Any] | None = None,
    ) -> None:
        try:
            _render_docx(
                result,
                output,
                title=title,
                user=user,
                header=header,
                profile=profile,
                layout=layout,
            )
        except ValueError as exc:
            if isinstance(exc, CompareError):
                raise
            raise CompareError(str(exc)) from exc

    @staticmethod
    def serialise(result: ComparisonResult) -> dict[str, Any]:
        return result.to_dict()


def audit_designer_config_path() -> Path:
    """Standardpfad des Originals: ``AUDIT_DOCUMENT_COMPARE_CONFIG`` oder ~/.config."""
    explicit = os.environ.get("AUDIT_DOCUMENT_COMPARE_CONFIG")
    if explicit:
        return Path(explicit).expanduser()
    return Path.home() / ".config" / "audit_designer" / "document_compare.json"


def read_document(path: str | Path, mode: str = "auto") -> list[dict[str, Any]]:
    """Jupyter-Einstieg: Zwischenmodell einer Quelle als Datensätze."""
    _resolved_mode, items = DocumentCompareService.read(Path(path), mode)
    return [asdict(item) for item in items]


def compare_documents(
    old: str | Path,
    new: str | Path,
    *,
    output: str | Path | None = None,
    config: str | Path | None = None,
    reason_provider: ReasonProvider | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    """CLI-/Jupyter-Einstieg des Originals: vergleichen und neben der neuen Fassung ablegen.

    Eingabedateien werden nicht verschoben oder gelöscht. Ohne ``config`` gilt
    der Standardpfad des Originals. Begründungen (``generate_reasons``)
    verlangen einen ``reason_provider`` oder den der Fassade.
    """
    old_path, new_path = Path(old), Path(new)
    department = load_settings(Path(config) if config else audit_designer_config_path())
    effective, sources = merge_settings(department, {}, overrides)
    result = DocumentCompareService.compare(
        old_path,
        new_path,
        mode=str(effective["mode"]),
        threshold=int(effective["threshold"]),
        include_answers=bool(effective["include_answers"]),
        include_notes=bool(effective["include_notes"]),
        include_editorial=bool(effective["include_editorial"]),
        highlight_words=bool(effective["highlight_words"]),
        output_sections=list(effective["output_sections"]),
        comparison_type=str(effective["comparison_type"]),
    )
    result.metadata["setting_sources"] = sources
    if effective.get("generate_reasons"):
        provider = reason_provider or DocumentCompareService.reason_provider
        if provider is None:
            raise CompareError("Begründungsvorschläge verlangen einen konfigurierten Dienst.")
        apply_reasons_cli(result, provider, str(effective.get("model") or "") or None)
    output_path = (
        Path(output)
        if output
        else new_path.with_name(f"Vergleich_{new_path.stem}_{date.today().isoformat()}.docx")
    )
    profile = str(effective.get("output_profile") or "memo")
    layout = dict(effective.get("text_layout" if profile == "text" else "memo_layout") or {})
    if overrides.get("header_text"):
        layout["header_text"] = str(overrides["header_text"])
    DocumentCompareService.render_docx(
        result,
        output_path,
        title=overrides.get("title"),
        user=str(overrides.get("user") or getpass.getuser()),
        profile=profile,
        layout=layout,
    )
    return {"output": str(output_path), **result.to_dict()}


def save_default_settings(path: Path | None = None) -> Path:
    """``--create-config`` des Originals."""
    target = path or audit_designer_config_path()
    save_settings({}, target)
    return target
