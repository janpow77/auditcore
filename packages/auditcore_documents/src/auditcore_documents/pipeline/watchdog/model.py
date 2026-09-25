"""Befundmodell, Eskalationsstufen und Schwellen des Extraktionsqualitäts-Watchdogs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from enum import StrEnum

# =============================================================================
# C-10: Dreistufiges Eskalationsmodell
# =============================================================================


class EscalationLevel(StrEnum):
    """Eskalationsstufen gemäß C-10."""

    INFO = "info"  # Stufe 1: Auffälligkeit dokumentiert
    WARNING = "warning"  # Stufe 2: Manuelle Nachprüfung empfohlen
    BLOCKER = "blocker"  # Stufe 3: Automatische Reporterstellung blockiert


class FindingCategory(StrEnum):
    """Kategorien für Watchdog-Befunde."""

    MANDATORY_FIELD = "mandatory_field"  # C-01
    DATE_VALIDATION = "date_validation"  # C-02
    INVOICE_NUMBER = "invoice_number"  # C-03
    CROSS_FIELD = "cross_field"  # C-04
    VAT_RATE = "vat_rate"  # C-05
    SUPPLIER_NAME = "supplier_name"  # C-06
    CONCENTRATION = "concentration"  # C-07
    SUM_RECONCILIATION = "sum_reconciliation"  # C-08
    DUPLICATE = "duplicate"  # C-09
    NAN_VALUE = "nan_value"  # A-07
    FORMAL_CORRECTNESS = "formal_correctness"  # B-12


# =============================================================================
# Dataclasses für Ergebnisse
# =============================================================================


@dataclass
class WatchdogFinding:
    """Einzelner Befund des Watchdog."""

    category: str
    level: str  # info, warning, blocker
    document_index: int | None  # Beleg-Nr. (0-basiert) oder None für Gesamtbefund
    field_name: str | None  # Betroffenes Feld oder None
    message_de: str
    message_en: str
    evidence: dict[str, object] = field(default_factory=dict)
    rule_reference: str = ""  # z.B. "§ 14 UStG"


@dataclass
class ExtractionQualityMetrics:
    """
    Extraktionsqualitäts-Metriken für den Report (C-12).

    Wird im Report-Abschnitt 'Extraktionsqualität' angezeigt.
    """

    total_documents: int = 0
    mandatory_fields_success_rate: float = 0.0  # 0.0 - 1.0
    per_field_success: dict[str, float] = field(default_factory=dict)
    documents_with_errors: int = 0
    documents_with_errors_rate: float = 0.0
    avg_ocr_confidence: float | None = None
    min_ocr_confidence: float | None = None
    escalated_documents: int = 0
    formal_correctness_rate: float = 0.0  # B-12: Tatsächliche formale Korrektheit


@dataclass
class WatchdogResult:
    """Gesamtergebnis des Watchdog-Durchlaufs."""

    findings: list[WatchdogFinding] = field(default_factory=list)
    metrics: ExtractionQualityMetrics = field(default_factory=ExtractionQualityMetrics)
    escalation_level: str = EscalationLevel.INFO
    report_blocked: bool = False
    block_reason: str | None = None
    timestamp: str = ""

    def to_json(self) -> str:
        """C-11: Export als maschinenlesbares JSON."""
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, default=str)


# =============================================================================
# Pflichtfelder gemäß § 14 UStG (C-01)
# =============================================================================

MANDATORY_FIELDS_USTG_14: dict[str, str] = {
    "supplier_name": "Name/Anschrift des Leistenden",
    "customer_name": "Name/Anschrift des Empfängers",
    "supplier_vat_id": "Steuernummer oder USt-IdNr.",
    "invoice_date": "Ausstellungsdatum",
    "invoice_number": "Fortlaufende Rechnungsnummer",
    "description": "Leistungsbeschreibung",
    "net_amount": "Entgelt (netto)",
    "vat_rate": "Steuersatz",
    "vat_amount": "Steuerbetrag",
}

# Gesetzlich zulässige Steuersätze (C-05)
VALID_VAT_RATES_DE: set[float] = {0.0, 7.0, 19.0}

# Toleranz für Querfeldplausibilität (C-04)
CROSS_FIELD_TOLERANCE: Decimal = Decimal("0.02")

# Maximale Länge für Rechnungsnummern (C-03)
MAX_INVOICE_NUMBER_LENGTH: int = 30

# Schwelle für Lieferantenkonzentration (C-07)
SUPPLIER_CONCENTRATION_THRESHOLD: float = 0.30  # 30%

# Schwelle für Eskalation Stufe 3 - Blockade (C-10)
ERROR_RATE_BLOCK_THRESHOLD: float = 0.20  # 20%
