"""Bestandsprüfung über viele Belege als REST-Vertrag ``documents_batch_checks/1``.

Der Dienst prüft einen übergebenen Bestand (Datensätze aus einer Tabelle oder
Ergebnisse der Belegerkennung ``documents_extraction/1``) mit dem
Extraktionsqualitäts-Watchdog (C-01 bis C-13, A-07, B-12) und den
Ergänzungsprüfungen ERG-01 (Nummernlücken) und ERG-02 (USt-IdNr.-Konsistenz).
Er liefert Befunde je Regel mit Begründung und betroffenen Belegen, die
Kennzahlen (C-12) und die Eskalation (C-10); der Export (C-11) wiederholt
den Lauf aus derselben Anfrage. Nur Standardbibliothek; der Dienst speichert
nichts. Vertrag: ``docs/ui/batch-checks-rest.md`` im Repository.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from auditcore_common.rest import choice, json_object

from auditcore_documents import __version__
from auditcore_documents.pipeline.watchdog import (
    ExtractionQualityWatchdog,
    WatchdogResult,
)
from auditcore_documents.pipeline.watchdog.cache import prepared_run
from auditcore_documents.pipeline.watchdog.inventory_checks import (
    check_invoice_number_gaps,
    check_vat_id_consistency,
)
from auditcore_documents.web.batch_export import EXPORT_FORMATS, export_answer
from auditcore_documents.web.batch_input import (
    BatchCheckError,
    BatchOptions,
    Inventory,
    field_catalogue,
    parse_inventory,
)
from auditcore_documents.web.batch_result import (
    LEVEL_LABELS,
    document_entries,
    finding_entries,
    metrics,
    rule_entries,
    summary,
)
from auditcore_documents.web.batch_rules import RULES
from auditcore_documents.web.export import ExportFile

CONTRACT = "documents_batch_checks/1"
LIBRARY = f"auditcore_documents {__version__}"


@dataclass(frozen=True)
class BatchCheckSettings:
    """Grenzen der Anwendung: Belege je Anfrage und Größe des Anfragekörpers."""

    max_documents: int = 5000
    max_body_bytes: int = 16 * 1024 * 1024


def _plain(value: object) -> object:
    """JSON-taugliche Kopie (Decimal und Aufzählungen als Text)."""
    loaded: object = json.loads(json.dumps(value, default=str, ensure_ascii=False))
    return loaded


class BatchCheckService:
    """Anwendungsfälle der Bestandsprüfung (Katalog, Prüflauf, Export)."""

    def __init__(
        self,
        settings: BatchCheckSettings | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.settings = settings or BatchCheckSettings()
        self.clock = clock or (lambda: datetime.now(UTC))

    def catalogue(self) -> dict[str, object]:
        """``GET /catalogue``: Regeln, Felder, Vorgaben, Stufen, Grenzen und Exportformate."""
        return {
            "contract": CONTRACT,
            "library": LIBRARY,
            "rules": [rule.to_dict() for rule in RULES],
            "fields": field_catalogue(),
            "defaults": BatchOptions().to_dict(),
            "levels": [{"id": str(k), "label": v} for k, v in LEVEL_LABELS.items()],
            "limits": {
                "max_documents": self.settings.max_documents,
                "max_body_bytes": self.settings.max_body_bytes,
            },
            "export_formats": list(EXPORT_FORMATS),
            "stored": False,
        }

    def _validate(self, inventory: Inventory) -> WatchdogResult:
        options = inventory.options
        watchdog = ExtractionQualityWatchdog(
            tolerance=options.tolerance,
            block_threshold=options.block_threshold,
            concentration_threshold=options.concentration_threshold,
            clock=self.clock,
        )
        documents = list(inventory.documents)
        confidences = list(inventory.confidences)
        result = watchdog.validate(
            documents,
            total_volume=options.total_volume,
            ocr_confidences=confidences if any(c is not None for c in confidences) else None,
        )
        if options.supplementary:
            check_invoice_number_gaps(documents, result)
            check_vat_id_consistency(documents, result)
        return result

    @prepared_run
    def check(self, payload: object) -> dict[str, object]:
        """``POST /runs``: Bestand prüfen; Befunde je Regel mit betroffenen Belegen."""
        inventory = parse_inventory(payload, self.settings.max_documents)
        result = self._validate(inventory)
        findings = finding_entries(result, inventory.documents)
        answer = {
            "contract": CONTRACT,
            "library": LIBRARY,
            "options": inventory.options.to_dict(),
            "summary": summary(result, findings, len(inventory.documents)),
            "metrics": metrics(result),
            "rules": rule_entries(findings, result, inventory),
            "findings": findings,
            "documents": document_entries(findings, inventory),
            "stored": False,
        }
        plain = _plain(answer)
        return plain if isinstance(plain, dict) else {}

    def export(self, payload: object) -> ExportFile:
        """``POST /export``: Lauf aus derselben Anfrage als JSON (C-11) oder CSV."""
        body = json_object(payload, "Anfrage", error=BatchCheckError)
        fmt = choice(body.get("format"), "format", EXPORT_FORMATS, error=BatchCheckError)
        answer = self.check({k: v for k, v in body.items() if k != "format"})
        return export_answer(answer, fmt)
