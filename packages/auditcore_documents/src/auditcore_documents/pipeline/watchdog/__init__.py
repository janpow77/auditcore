"""Extraktionsqualitäts-Watchdog (aus flowinvoice ``services/extraction_quality_watchdog.py``).

Validiert OCR-/Extraktionsergebnisse vor Aufnahme in den Bericht
(Anforderungen C-01 bis C-13 des Verbesserungskatalogs HA-EFRE-2026-0847).

Quelle: janpow77/flowinvoice@fb2d18568d2eaf64574d131ceae51a936b9aac02,
Blob 16f5e7a071e7e59b6f862d2a1ac1416132cdea76 (Verbraucher im Original:
``api/fraud_detection.py``).

Entscheidung D8 (2026-09-23, Nutzerzitat „alle empfehlungen“): übernommen
mit korrekten Umlauten in allen deutschen Meldungstexten (``message_de``,
``block_reason``, Mängelliste). Das ist die einzige beabsichtigte
Abweichung; nach Rückumschrift (ä→ae, ö→oe, ü→ue, ß→ss) stimmen die
Ergebnisse mit dem Original überein (``tests/test_watchdog.py``).
Eingabemuster (z. B. „steuer“, „adresse“) sind unverändert. Das Logging
des Originals entfällt; die Uhr für den Zeitstempel ist injizierbar.

Referenzen:
    - § 14 UStG (Pflichtangaben auf Rechnungen)
    - § 12 UStG (Steuersätze)
    - Art. 74 Abs. 1 lit. a VO (EU) 2021/1060 (zuverlässige Daten)
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, date, datetime
from decimal import Decimal

from .document_checks import (
    check_cross_field_plausibility,
    check_dates,
    check_invoice_numbers,
    check_mandatory_fields,
    check_nan_values,
    check_supplier_names,
    check_vat_rates,
)
from .model import (
    CROSS_FIELD_TOLERANCE,
    ERROR_RATE_BLOCK_THRESHOLD,
    MANDATORY_FIELDS_USTG_14,
    MAX_INVOICE_NUMBER_LENGTH,
    SUPPLIER_CONCENTRATION_THRESHOLD,
    VALID_VAT_RATES_DE,
    EscalationLevel,
    ExtractionQualityMetrics,
    FindingCategory,
    WatchdogFinding,
    WatchdogResult,
)
from .portfolio_checks import (
    calculate_formal_correctness,
    calculate_ocr_metrics,
    check_duplicates,
    check_sum_reconciliation,
    check_supplier_concentration,
    determine_escalation,
)

__all__ = [
    "CROSS_FIELD_TOLERANCE",
    "ERROR_RATE_BLOCK_THRESHOLD",
    "MANDATORY_FIELDS_USTG_14",
    "MAX_INVOICE_NUMBER_LENGTH",
    "SUPPLIER_CONCENTRATION_THRESHOLD",
    "VALID_VAT_RATES_DE",
    "EscalationLevel",
    "ExtractionQualityMetrics",
    "ExtractionQualityWatchdog",
    "FindingCategory",
    "WatchdogFinding",
    "WatchdogResult",
    "validate_extraction_quality",
]


class ExtractionQualityWatchdog:
    """
    Zentraler Qualitäts-Watchdog für die OCR-/Extraktionspipeline.

    Implementiert die Anforderungen C-01 bis C-13 des Verbesserungskatalogs.
    Muss zwischen Extraktion und Report-Generierung laufen.

    Verwendung:
        watchdog = ExtractionQualityWatchdog()
        result = watchdog.validate(documents, total_volume=74876.29)

        if result.report_blocked:
            # Manuelle Freigabe erforderlich
            notify_reviewer(result)
        else:
            # Report kann generiert werden
            generate_report(documents, quality_metrics=result.metrics)
    """

    def __init__(
        self,
        execution_period_start: date | None = None,
        execution_period_end: date | None = None,
        tolerance: Decimal = CROSS_FIELD_TOLERANCE,
        block_threshold: float = ERROR_RATE_BLOCK_THRESHOLD,
        concentration_threshold: float = SUPPLIER_CONCENTRATION_THRESHOLD,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.execution_period_start = execution_period_start
        self.execution_period_end = execution_period_end
        self.tolerance = tolerance
        self.block_threshold = block_threshold
        self.concentration_threshold = concentration_threshold
        self.clock = clock or (lambda: datetime.now(UTC))

    def validate(
        self,
        documents: Sequence[Mapping[str, object]],
        total_volume: float | None = None,
        ocr_confidences: Sequence[float | None] | None = None,
    ) -> WatchdogResult:
        """
        Führt alle Watchdog-Prüfungen auf extrahierten Belegen durch.

        Args:
            documents: Liste von extrahierten Beleg-Dicts mit Feldern wie
                       invoice_number, invoice_date, supplier_name, net_amount,
                       vat_amount, gross_amount, vat_rate, etc.
            total_volume: Ausgewiesenes Gesamtvolumen (für C-08 Summenabgleich).
            ocr_confidences: Optional, OCR-Confidence pro Beleg (0.0-1.0).

        Returns:
            WatchdogResult mit allen Befunden und Metriken.
        """
        result = WatchdogResult(timestamp=self.clock().isoformat())
        result.metrics.total_documents = len(documents)
        if not documents:
            return result
        check_mandatory_fields(documents, result)  # C-01
        check_dates(documents, result)  # C-02
        check_invoice_numbers(documents, result)  # C-03
        check_cross_field_plausibility(documents, result, self.tolerance)  # C-04
        check_vat_rates(documents, result)  # C-05
        check_supplier_names(documents, result)  # C-06
        check_supplier_concentration(documents, result, self.concentration_threshold)  # C-07
        if total_volume is not None:
            check_sum_reconciliation(documents, total_volume, result)  # C-08
        check_duplicates(documents, result)  # C-09
        check_nan_values(documents, result)  # A-07
        calculate_formal_correctness(documents, result)  # B-12
        if ocr_confidences:
            calculate_ocr_metrics(ocr_confidences, result)  # C-12/C-13
        determine_escalation(result, self.block_threshold)  # C-10
        return result


def validate_extraction_quality(
    documents: Sequence[Mapping[str, object]],
    total_volume: float | None = None,
    ocr_confidences: Sequence[float | None] | None = None,
    execution_period_start: date | None = None,
    execution_period_end: date | None = None,
) -> WatchdogResult:
    """
    Convenience-Funktion für Extraktionsqualitäts-Validierung.

    Args:
        documents: Liste extrahierter Beleg-Dicts.
        total_volume: Ausgewiesenes Gesamtvolumen.
        ocr_confidences: OCR-Confidence pro Beleg.
        execution_period_start: Start des Durchführungszeitraums.
        execution_period_end: Ende des Durchführungszeitraums.

    Returns:
        WatchdogResult mit Befunden und Metriken.
    """
    watchdog = ExtractionQualityWatchdog(
        execution_period_start=execution_period_start,
        execution_period_end=execution_period_end,
    )
    return watchdog.validate(
        documents=documents,
        total_volume=total_volume,
        ocr_confidences=ocr_confidences,
    )
