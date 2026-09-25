"""Optionale maschinelle Begründungsvorschläge über einen injizierbaren Port.

Das Original rief lazy ``app.modules.standards.mcp_tools.ausfuehren(
"document_compare_reason", {...})`` auf (FlowAgent). Die Bibliothek kennt
keinen KI-Dienst: Die Anwendung übergibt einen ``ReasonProvider``. Geprüft
wird ausschließlich, ob in Begründung und Rechtsgrundlage genannte
Fundstellen im alten oder neuen Wortlaut vorkommen; das ist keine
inhaltliche Richtigkeitsprüfung. Die Würdigung bleibt beim Prüfer.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from typing import Any, Protocol

from auditcore_documents.errors import CompareError
from auditcore_documents.model import CompareRow, ComparisonResult

LEGAL_REFERENCE_RE = re.compile(
    r"(?:"
    r"§+\s*\d+[a-z]?(?:\s*(?:Abs\.?|Absatz)\s*\d+)?"
    r"|Art(?:ikel)?\.?\s*\d+[a-z]?"
    r"|(?:VO\s*)?\(EU\)\s*\d{4}/\d+"
    r")",
    re.IGNORECASE,
)
METADATA_KEYS = ("provider", "prompt_version", "temperature", "seed", "quantization")
WORKER_PROMPT_VERSION = "document-compare-reason-v1"


class ReasonProvider(Protocol):
    """Liefert die Rohantwort (JSON-Text oder Mapping) für einen Begründungsvorschlag."""

    def __call__(
        self, old_text: str, new_text: str, model: str | None
    ) -> str | Mapping[str, Any]: ...


def mcp_tool_provider(
    execute: Callable[[str, dict[str, Any]], str], tool: str = "document_compare_reason"
) -> ReasonProvider:
    """Adapter für eine MCP-Werkzeugfunktion mit dem Aufrufvertrag des Originals."""

    def provider(old_text: str, new_text: str, model: str | None) -> str:
        return execute(tool, {"alt": old_text, "neu": new_text, "modell": model})

    return provider


def _reference_key(value: str) -> str:
    return re.sub(r"[\s.,;:()]+", "", value or "").casefold()


def verify_legal_references(
    reason: str, legal_basis: str, old_text: str, new_text: str
) -> tuple[bool, list[str]]:
    """Genannte Fundstellen, die in keiner Fassung stehen (sortiert)."""
    references = {
        match.group(0).strip() for match in LEGAL_REFERENCE_RE.finditer(f"{reason} {legal_basis}")
    }
    source_key = _reference_key(f"{old_text} {new_text}")
    missing = sorted(
        reference for reference in references if _reference_key(reference) not in source_key
    )
    return not missing, missing


def generate_reason(
    old_text: str,
    new_text: str,
    model: str | None = None,
    *,
    provider: ReasonProvider,
) -> tuple[str, dict[str, Any]]:
    """Vorschlag erzeugen und Fundstellen prüfen (Vertrag des Originals)."""
    raw = provider(old_text, new_text, model)
    if isinstance(raw, Mapping):
        payload: object = dict(raw)
    else:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CompareError("FlowAgent hat keine gültige JSON-Begründung geliefert.") from exc
    if not isinstance(payload, dict):
        # Original: AttributeError bei payload.get; hier ein fachlicher Fehler (DC-C06).
        raise CompareError("FlowAgent hat keine gültige JSON-Begründung geliefert.")
    reason_text = str(payload.get("begruendung", "")).strip()
    legal_basis = str(payload.get("rechtsgrundlage", "")).strip()
    verified, missing = verify_legal_references(reason_text, legal_basis, old_text, new_text)
    reason = " ".join(value for value in (reason_text, legal_basis) if value).strip()
    metadata = {key: payload[key] for key in METADATA_KEYS if key in payload} | {
        "model": model or "configured",
        "verified": verified,
        "missing_references": missing,
    }
    return reason, metadata


def _joined(row: CompareRow, side: str) -> str:
    values = [getattr(row, f"{side}_{name}") for name in ("text", "answer", "comment", "note")]
    return "\n".join(filter(None, values))


def apply_reasons_worker(
    result: ComparisonResult,
    provider: ReasonProvider,
    model: str | None = None,
    *,
    on_progress: Callable[[int], None] | None = None,
    on_error: Callable[[CompareRow, Exception], None] | None = None,
) -> dict[str, Any]:
    """Begründungen wie die Celery-Aufgabe des Originals (Vorschau-Workflow).

    Nur ausgewählte geänderte Zeilen; Eingabe sind Text, Antwort, Bemerkung
    und Hinweis. Scheitert der Dienst für eine Zeile, erhält sie einen
    sichtbaren Platzhalter statt eines Abbruchs. Fortschritt 35–95 %.
    Die Bibliothek protokolliert nicht; ``on_error`` übernimmt das.
    """
    llm_meta: dict[str, Any] = {
        "provider": "flowagent",
        "model": model or "configured",
        "temperature": 0.0,
        "prompt_version": WORKER_PROMPT_VERSION,
    }
    changed_rows = [row for row in result.rows if row.status == "changed"]
    for index, row in enumerate(changed_rows, start=1):
        if not row.selected:
            continue
        try:
            row.reason, llm_meta = generate_reason(
                _joined(row, "old"), _joined(row, "new"), model, provider=provider
            )
            row.reason_source = "flowagent"
            row.reason_verified = bool(llm_meta.get("verified", False))
            missing = llm_meta.get("missing_references") or []
            if missing:
                row.reason_warning = "Nicht in den Fassungen belegte Fundstelle: " + ", ".join(
                    str(value) for value in missing
                )
        except Exception as exc:  # noqa: BLE001 - Originalvertrag: Zeile markieren, weiter
            if on_error is not None:
                on_error(row, exc)
            row.reason = f"[FlowAgent-Vorschlag nicht verfügbar: {exc}]"
            row.reason_source = "flowagent"
            row.reason_verified = False
        if on_progress is not None:
            on_progress(min(95, 35 + round(60 * index / max(1, len(changed_rows)))))
    result.metadata["llm"] = llm_meta
    return llm_meta


def apply_reasons_cli(
    result: ComparisonResult, provider: ReasonProvider, model: str | None = None
) -> None:
    """Begründungen wie ``compare_documents`` (CLI/Jupyter) des Originals.

    Alle geänderten Zeilen, Eingabe „Text\\nHinweis“, Fehler brechen ab.
    """
    metadata: dict[str, Any] = {}
    for row in result.rows:
        if row.status != "changed":
            continue
        row.reason, metadata = generate_reason(
            f"{row.old_text}\n{row.old_note}",
            f"{row.new_text}\n{row.new_note}",
            model,
            provider=provider,
        )
        row.reason_source = "flowagent"
        row.reason_verified = bool(metadata.get("verified"))
        missing = metadata.get("missing_references") or []
        if missing:
            row.reason_warning = "Nicht belegt: " + ", ".join(missing)
    if metadata:
        result.metadata["llm"] = metadata
