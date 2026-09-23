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

import json
import math
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any

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
    evidence: dict[str, Any] = field(default_factory=dict)
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
        documents: list[dict[str, Any]],
        total_volume: float | None = None,
        ocr_confidences: list[float | None] | None = None,
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
        n = len(documents)
        result.metrics.total_documents = n

        if n == 0:
            return result

        # C-01: Pflichtfeldvalidierung
        self._check_mandatory_fields(documents, result)

        # C-02: Datumsvalidierung
        self._check_dates(documents, result)

        # C-03: Rechnungsnummern-Plausibilität
        self._check_invoice_numbers(documents, result)

        # C-04: Querfeldplausibilität
        self._check_cross_field_plausibility(documents, result)

        # C-05: Steuersatz-Validierung
        self._check_vat_rates(documents, result)

        # C-06: Lieferantennamen-Plausibilität
        self._check_supplier_names(documents, result)

        # C-07: Lieferanten-Konzentrationsrisiko
        self._check_supplier_concentration(documents, result)

        # C-08: Summenabgleich
        if total_volume is not None:
            self._check_sum_reconciliation(documents, total_volume, result)

        # C-09: Duplikatprüfung
        self._check_duplicates(documents, result)

        # A-07: NaN/Null/undefined-Prüfung
        self._check_nan_values(documents, result)

        # B-12: Formale Korrektheit berechnen
        self._calculate_formal_correctness(documents, result)

        # C-12/C-13: OCR-Confidence-Metriken
        if ocr_confidences:
            self._calculate_ocr_metrics(ocr_confidences, result)

        # C-10: Eskalationsstufe bestimmen
        self._determine_escalation(result)

        return result

    # =========================================================================
    # C-01: Pflichtfeldvalidierung (§ 14 UStG)
    # =========================================================================

    def _check_mandatory_fields(
        self,
        documents: list[dict[str, Any]],
        result: WatchdogResult,
    ) -> None:
        """Prüft jeden Beleg gegen die Pflichtfeldliste nach § 14 UStG."""
        field_success_counts: dict[str, int] = dict.fromkeys(MANDATORY_FIELDS_USTG_14, 0)
        docs_with_missing = 0

        for idx, doc in enumerate(documents):
            missing = []
            for field_key, field_desc in MANDATORY_FIELDS_USTG_14.items():
                value = doc.get(field_key)
                if self._is_empty_or_invalid(value):
                    missing.append(field_desc)
                else:
                    field_success_counts[field_key] += 1

            if missing:
                docs_with_missing += 1
                result.findings.append(
                    WatchdogFinding(
                        category=FindingCategory.MANDATORY_FIELD,
                        level=EscalationLevel.WARNING,
                        document_index=idx,
                        field_name=None,
                        message_de=(
                            f"Beleg {idx + 1}: {len(missing)} Pflichtfeld(er) "
                            f"fehlen: {', '.join(missing)}"
                        ),
                        message_en=(
                            f"Document {idx + 1}: {len(missing)} mandatory "
                            f"field(s) missing: {', '.join(missing)}"
                        ),
                        evidence={"missing_fields": missing},
                        rule_reference="§ 14 UStG",
                    )
                )

        n = len(documents)
        total_fields = len(MANDATORY_FIELDS_USTG_14)
        total_checks = n * total_fields
        successful_checks = sum(field_success_counts.values())

        result.metrics.mandatory_fields_success_rate = (
            successful_checks / total_checks if total_checks > 0 else 0.0
        )
        result.metrics.per_field_success = {
            k: v / n if n > 0 else 0.0 for k, v in field_success_counts.items()
        }
        result.metrics.documents_with_errors = docs_with_missing
        result.metrics.documents_with_errors_rate = docs_with_missing / n if n > 0 else 0.0

    # =========================================================================
    # C-02: Datumsvalidierung
    # =========================================================================

    def _check_dates(self, documents: list[dict[str, Any]], result: WatchdogResult) -> None:
        """Validiert Datumsfelder: kein 'Invalid Date', gültiges Format."""
        date_patterns = [
            re.compile(r"^\d{2}\.\d{2}\.\d{4}$"),  # TT.MM.JJJJ
            re.compile(r"^\d{4}-\d{2}-\d{2}$"),  # JJJJ-MM-TT
        ]

        invalid_date_markers = {
            "invalid date",
            "nan",
            "null",
            "undefined",
            "n/a",
            "none",
        }

        for idx, doc in enumerate(documents):
            date_val = doc.get("invoice_date", "")
            if not date_val:
                continue

            date_str = str(date_val).strip()

            # Prüfe auf bekannte Fehlerwerte
            if date_str.lower() in invalid_date_markers:
                result.findings.append(
                    WatchdogFinding(
                        category=FindingCategory.DATE_VALIDATION,
                        level=EscalationLevel.WARNING,
                        document_index=idx,
                        field_name="invoice_date",
                        message_de=(
                            f"Beleg {idx + 1}: Datum nicht extrahierbar "
                            f"(Wert: '{date_str}'). Manuelle Nachprüfung erforderlich."
                        ),
                        message_en=(
                            f"Document {idx + 1}: Date not extractable "
                            f"(value: '{date_str}'). Manual review required."
                        ),
                        evidence={"raw_value": date_str},
                    )
                )
                continue

            # Prüfe Format
            if not any(p.match(date_str) for p in date_patterns):
                # Versuche trotzdem zu parsen
                parsed = self._try_parse_date(date_str)
                if not parsed:
                    result.findings.append(
                        WatchdogFinding(
                            category=FindingCategory.DATE_VALIDATION,
                            level=EscalationLevel.WARNING,
                            document_index=idx,
                            field_name="invoice_date",
                            message_de=(
                                f"Beleg {idx + 1}: Datumsformat unbekannt "
                                f"(Wert: '{date_str}'). Erwartet: TT.MM.JJJJ oder JJJJ-MM-TT."
                            ),
                            message_en=(
                                f"Document {idx + 1}: Unknown date format "
                                f"(value: '{date_str}'). Expected: DD.MM.YYYY or YYYY-MM-DD."
                            ),
                            evidence={"raw_value": date_str},
                        )
                    )

    # =========================================================================
    # C-03: Rechnungsnummern-Plausibilität
    # =========================================================================

    def _check_invoice_numbers(
        self, documents: list[dict[str, Any]], result: WatchdogResult
    ) -> None:
        """Prüft Rechnungsnummern auf plausible Muster."""
        for idx, doc in enumerate(documents):
            inv_nr = doc.get("invoice_number", "")
            if not inv_nr:
                continue

            inv_str = str(inv_nr).strip()
            issues: list[str] = []

            # Längenprüfung
            if len(inv_str) > MAX_INVOICE_NUMBER_LENGTH:
                issues.append(f"zu lang ({len(inv_str)} > {MAX_INVOICE_NUMBER_LENGTH} Zeichen)")

            # Fließtext-Erkennung: enthält Leerzeichen und Wörter
            words = inv_str.split()
            if len(words) > 3:
                issues.append("sieht nach Fließtext aus, nicht nach Rechnungsnummer")

            # Bekannte Fehlmuster
            lower = inv_str.lower()
            suspicious_patterns = [
                "erneuerbar",
                "ust:",
                "ust-id",
                "steuer",
                "adresse",
                "telefon",
                "email",
                "www.",
                "http",
            ]
            for pattern in suspicious_patterns:
                if pattern in lower:
                    issues.append(f"verdächtiger Inhalt (enthält '{pattern}')")
                    break

            # Prüfen ob alphanumerisch (mit gängigen Trennzeichen)
            cleaned = re.sub(r"[A-Za-z0-9\-_/.]", "", inv_str)
            if len(cleaned) > len(inv_str) * 0.3:
                issues.append("zu viele Sonderzeichen für eine Rechnungsnummer")

            if issues:
                result.findings.append(
                    WatchdogFinding(
                        category=FindingCategory.INVOICE_NUMBER,
                        level=EscalationLevel.WARNING,
                        document_index=idx,
                        field_name="invoice_number",
                        message_de=(
                            f"Beleg {idx + 1}: Rechnungsnummer '{inv_str}' "
                            f"nicht plausibel: {'; '.join(issues)}"
                        ),
                        message_en=(
                            f"Document {idx + 1}: Invoice number '{inv_str}' "
                            f"implausible: {'; '.join(issues)}"
                        ),
                        evidence={"value": inv_str, "issues": issues},
                    )
                )

    # =========================================================================
    # C-04: Querfeldplausibilität
    # =========================================================================

    def _check_cross_field_plausibility(
        self, documents: list[dict[str, Any]], result: WatchdogResult
    ) -> None:
        """Prüft Brutto = Netto + Steuerbetrag."""
        for idx, doc in enumerate(documents):
            net = self._to_decimal(doc.get("net_amount"))
            vat = self._to_decimal(doc.get("vat_amount"))
            gross = self._to_decimal(doc.get("gross_amount"))

            if net is None or vat is None or gross is None:
                continue

            calculated = net + vat
            diff = abs(gross - calculated)

            if diff > self.tolerance:
                result.findings.append(
                    WatchdogFinding(
                        category=FindingCategory.CROSS_FIELD,
                        level=EscalationLevel.WARNING,
                        document_index=idx,
                        field_name=None,
                        message_de=(
                            f"Beleg {idx + 1}: Brutto ({gross}) != "
                            f"Netto ({net}) + USt ({vat}) = {calculated}. "
                            f"Differenz: {diff} EUR."
                        ),
                        message_en=(
                            f"Document {idx + 1}: Gross ({gross}) != "
                            f"Net ({net}) + VAT ({vat}) = {calculated}. "
                            f"Difference: {diff} EUR."
                        ),
                        evidence={
                            "net": str(net),
                            "vat": str(vat),
                            "gross": str(gross),
                            "calculated": str(calculated),
                            "difference": str(diff),
                        },
                    )
                )

            # Steuerbetrag = Netto x Steuersatz
            vat_rate = self._to_decimal(doc.get("vat_rate"))
            if vat_rate is not None and net is not None:
                expected_vat = net * vat_rate / Decimal("100")
                vat_diff = abs(vat - expected_vat) if vat is not None else None
                if vat_diff is not None and vat_diff > self.tolerance:
                    result.findings.append(
                        WatchdogFinding(
                            category=FindingCategory.CROSS_FIELD,
                            level=EscalationLevel.INFO,
                            document_index=idx,
                            field_name="vat_amount",
                            message_de=(
                                f"Beleg {idx + 1}: USt ({vat}) != "
                                f"Netto ({net}) x {vat_rate}% = {expected_vat:.2f}."
                            ),
                            message_en=(
                                f"Document {idx + 1}: VAT ({vat}) != "
                                f"Net ({net}) x {vat_rate}% = {expected_vat:.2f}."
                            ),
                            evidence={
                                "vat": str(vat),
                                "expected_vat": str(expected_vat),
                                "vat_rate": str(vat_rate),
                            },
                        )
                    )

    # =========================================================================
    # C-05: Steuersatz-Validierung
    # =========================================================================

    def _check_vat_rates(self, documents: list[dict[str, Any]], result: WatchdogResult) -> None:
        """Prüft Steuersätze gegen gesetzlich zulässige Werte."""
        rates_seen: dict[float, int] = {}
        for idx, doc in enumerate(documents):
            rate = self._to_float(doc.get("vat_rate"))
            if rate is None:
                continue

            rates_seen[rate] = rates_seen.get(rate, 0) + 1

            if rate not in VALID_VAT_RATES_DE:
                result.findings.append(
                    WatchdogFinding(
                        category=FindingCategory.VAT_RATE,
                        level=EscalationLevel.WARNING,
                        document_index=idx,
                        field_name="vat_rate",
                        message_de=(
                            f"Beleg {idx + 1}: Steuersatz {rate}% entspricht "
                            f"keinem gesetzlich zulässigen Satz (0%, 7%, 19%)."
                        ),
                        message_en=(
                            f"Document {idx + 1}: VAT rate {rate}% does not match "
                            f"any legally permitted rate (0%, 7%, 19%)."
                        ),
                        evidence={"vat_rate": rate, "valid_rates": sorted(VALID_VAT_RATES_DE)},
                        rule_reference="§ 12 UStG",
                    )
                )

        # Hinweis: Wenn alle den gleichen Satz haben, könnte es ein Default sein
        if len(rates_seen) == 1 and len(documents) > 5:
            rate = next(iter(rates_seen))
            result.findings.append(
                WatchdogFinding(
                    category=FindingCategory.VAT_RATE,
                    level=EscalationLevel.INFO,
                    document_index=None,
                    field_name="vat_rate",
                    message_de=(
                        f"Alle {len(documents)} Belege zeigen identischen "
                        f"Steuersatz ({rate}%). Möglicherweise Default-Wert "
                        f"statt tatsächlich extrahiertem Wert."
                    ),
                    message_en=(
                        f"All {len(documents)} documents show identical "
                        f"VAT rate ({rate}%). Possibly default value "
                        f"instead of actually extracted value."
                    ),
                    evidence={"uniform_rate": rate, "document_count": len(documents)},
                )
            )

    # =========================================================================
    # C-06: Lieferantennamen-Plausibilität
    # =========================================================================

    def _check_supplier_names(
        self, documents: list[dict[str, Any]], result: WatchdogResult
    ) -> None:
        """Prüft Lieferantennamen auf Plausibilität."""
        for idx, doc in enumerate(documents):
            name = doc.get("supplier_name", "")
            if not name:
                continue

            name_str = str(name).strip()
            issues: list[str] = []

            # Kein Großbuchstabe
            if name_str == name_str.lower() and len(name_str) > 2:
                issues.append("kein Großbuchstabe (kein plausibler Firmen-/Personenname)")

            # Zu kurz (einzelnes Wort unter 3 Zeichen)
            if len(name_str) < 3:
                issues.append(f"zu kurz ({len(name_str)} Zeichen)")

            # Nur Zahlen
            if name_str.replace(" ", "").isdigit():
                issues.append("besteht nur aus Zahlen")

            if issues:
                result.findings.append(
                    WatchdogFinding(
                        category=FindingCategory.SUPPLIER_NAME,
                        level=EscalationLevel.WARNING,
                        document_index=idx,
                        field_name="supplier_name",
                        message_de=(
                            f"Beleg {idx + 1}: Lieferantenname '{name_str}' "
                            f"nicht plausibel: {'; '.join(issues)}"
                        ),
                        message_en=(
                            f"Document {idx + 1}: Supplier name '{name_str}' "
                            f"implausible: {'; '.join(issues)}"
                        ),
                        evidence={"value": name_str, "issues": issues},
                    )
                )

    # =========================================================================
    # C-07: Lieferanten-Konzentrationsrisiko
    # =========================================================================

    def _check_supplier_concentration(
        self, documents: list[dict[str, Any]], result: WatchdogResult
    ) -> None:
        """Prüft ob ein einzelner Lieferant mehr als 30% des Volumens ausmacht."""
        supplier_volumes: dict[str, Decimal] = {}
        supplier_counts: dict[str, int] = {}
        total = Decimal("0")

        for doc in documents:
            name = self._normalize_supplier_name(doc.get("supplier_name", ""))
            if not name:
                continue

            amount = self._to_decimal(doc.get("gross_amount") or doc.get("net_amount"))
            if amount is None:
                amount = Decimal("0")

            supplier_volumes[name] = supplier_volumes.get(name, Decimal("0")) + amount
            supplier_counts[name] = supplier_counts.get(name, 0) + 1
            total += amount

        if total <= 0:
            return

        for supplier, volume in supplier_volumes.items():
            share = float(volume / total)
            if share > self.concentration_threshold:
                count = supplier_counts.get(supplier, 0)
                result.findings.append(
                    WatchdogFinding(
                        category=FindingCategory.CONCENTRATION,
                        level=EscalationLevel.WARNING,
                        document_index=None,
                        field_name="supplier_name",
                        message_de=(
                            f"Konzentrationsrisiko: '{supplier}' hat {count} "
                            f"Belege ({share:.1%} des Gesamtvolumens)."
                        ),
                        message_en=(
                            f"Concentration risk: '{supplier}' has {count} "
                            f"documents ({share:.1%} of total volume)."
                        ),
                        evidence={
                            "supplier": supplier,
                            "document_count": count,
                            "volume": str(volume),
                            "share": round(share, 4),
                        },
                    )
                )

    # =========================================================================
    # C-08: Summenabgleich
    # =========================================================================

    def _check_sum_reconciliation(
        self,
        documents: list[dict[str, Any]],
        total_volume: float,
        result: WatchdogResult,
    ) -> None:
        """Prüft ob Summe der Einzelbeträge dem Gesamtvolumen entspricht."""
        calculated_sum = Decimal("0")
        for doc in documents:
            amount = self._to_decimal(doc.get("gross_amount") or doc.get("net_amount"))
            if amount is not None:
                calculated_sum += amount

        total_dec = Decimal(str(total_volume))
        diff = abs(calculated_sum - total_dec)

        # Toleranz: 1 Cent pro Beleg (Rundungsdifferenzen)
        tolerance = Decimal(str(len(documents) * 0.01))

        if diff > tolerance:
            result.findings.append(
                WatchdogFinding(
                    category=FindingCategory.SUM_RECONCILIATION,
                    level=EscalationLevel.WARNING,
                    document_index=None,
                    field_name=None,
                    message_de=(
                        f"Summenabweichung: Einzelbeträge ergeben {calculated_sum:.2f} EUR, "
                        f"ausgewiesenes Gesamtvolumen ist {total_dec:.2f} EUR. "
                        f"Differenz: {diff:.2f} EUR."
                    ),
                    message_en=(
                        f"Sum discrepancy: Individual amounts total {calculated_sum:.2f} EUR, "
                        f"reported total volume is {total_dec:.2f} EUR. "
                        f"Difference: {diff:.2f} EUR."
                    ),
                    evidence={
                        "calculated_sum": str(calculated_sum),
                        "reported_total": str(total_dec),
                        "difference": str(diff),
                    },
                )
            )

    # =========================================================================
    # C-09: Duplikatprüfung (Lieferant + Re.-Nr.)
    # =========================================================================

    def _check_duplicates(self, documents: list[dict[str, Any]], result: WatchdogResult) -> None:
        """Prüft auf identische Kombination Lieferant + Rechnungsnummer."""
        seen: dict[str, list[int]] = {}

        for idx, doc in enumerate(documents):
            supplier = self._normalize_supplier_name(doc.get("supplier_name", ""))
            inv_nr = str(doc.get("invoice_number", "")).strip()

            if not supplier or not inv_nr:
                continue

            key = f"{supplier}|{inv_nr}"
            if key not in seen:
                seen[key] = []
            seen[key].append(idx)

        for key, indices in seen.items():
            if len(indices) > 1:
                supplier, inv_nr = key.split("|", 1)
                result.findings.append(
                    WatchdogFinding(
                        category=FindingCategory.DUPLICATE,
                        level=EscalationLevel.WARNING,
                        document_index=indices[0],
                        field_name=None,
                        message_de=(
                            f"Mögliches Duplikat: Lieferant '{supplier}' mit "
                            f"Re.-Nr. '{inv_nr}' erscheint {len(indices)}x "
                            f"(Belege {', '.join(str(i + 1) for i in indices)})."
                        ),
                        message_en=(
                            f"Possible duplicate: Supplier '{supplier}' with "
                            f"invoice no. '{inv_nr}' appears {len(indices)}x "
                            f"(documents {', '.join(str(i + 1) for i in indices)})."
                        ),
                        evidence={
                            "supplier": supplier,
                            "invoice_number": inv_nr,
                            "document_indices": indices,
                        },
                    )
                )

    # =========================================================================
    # A-07: NaN/Null/undefined-Schutz
    # =========================================================================

    def _check_nan_values(self, documents: list[dict[str, Any]], result: WatchdogResult) -> None:
        """Prüft auf NaN, null, undefined in numerischen Feldern."""
        numeric_fields = [
            "net_amount",
            "vat_amount",
            "gross_amount",
            "vat_rate",
        ]
        nan_markers = {"nan", "null", "undefined", "none", "inf", "-inf", "n/a"}

        for idx, doc in enumerate(documents):
            for fld in numeric_fields:
                value = doc.get(fld)
                if value is None:
                    continue

                val_str = str(value).strip().lower()
                is_nan = val_str in nan_markers

                if not is_nan:
                    try:
                        f = float(value)
                        if math.isnan(f) or math.isinf(f):
                            is_nan = True
                    except (ValueError, TypeError):
                        pass

                if is_nan:
                    result.findings.append(
                        WatchdogFinding(
                            category=FindingCategory.NAN_VALUE,
                            level=EscalationLevel.WARNING,
                            document_index=idx,
                            field_name=fld,
                            message_de=(
                                f"Beleg {idx + 1}: Feld '{fld}' enthält "
                                f"ungültigen Wert '{value}'. "
                                f"Anzeige als 'n/v' (nicht verfügbar) erforderlich."
                            ),
                            message_en=(
                                f"Document {idx + 1}: Field '{fld}' contains "
                                f"invalid value '{value}'. "
                                f"Must display as 'n/a' (not available)."
                            ),
                            evidence={"field": fld, "raw_value": str(value)},
                        )
                    )

    # =========================================================================
    # B-12: Formale Korrektheit
    # =========================================================================

    def _calculate_formal_correctness(
        self, documents: list[dict[str, Any]], result: WatchdogResult
    ) -> None:
        """
        Berechnet die tatsächliche formale Korrektheit.

        Ein Beleg gilt als formal korrekt, wenn:
        - Alle Pflichtfelder vorhanden
        - Datum gültig (kein 'Invalid Date')
        - Rechnungsnummer plausibel
        - Keine NaN-Werte in numerischen Feldern
        """
        formally_correct = 0
        issues_per_doc: dict[int, list[str]] = {}

        for idx, doc in enumerate(documents):
            doc_issues: list[str] = []

            # Pflichtfelder prüfen
            for field_key in MANDATORY_FIELDS_USTG_14:
                if self._is_empty_or_invalid(doc.get(field_key)):
                    doc_issues.append(f"Pflichtfeld '{field_key}' fehlt")

            # Datum prüfen
            date_val = str(doc.get("invoice_date", "")).strip().lower()
            if date_val in {"invalid date", "nan", "null", "undefined", "n/a", "none", ""}:
                doc_issues.append("Datum ungültig")

            # Rechnungsnummer prüfen
            inv_nr = str(doc.get("invoice_number", "")).strip()
            if inv_nr and (len(inv_nr) > MAX_INVOICE_NUMBER_LENGTH or len(inv_nr.split()) > 3):
                doc_issues.append("Rechnungsnummer nicht plausibel")

            # NaN-Werte prüfen
            for fld in ["net_amount", "vat_amount", "gross_amount"]:
                val = doc.get(fld)
                if val is not None:
                    try:
                        f = float(val)
                        if math.isnan(f) or math.isinf(f):
                            doc_issues.append(f"NaN/Inf in '{fld}'")
                    except (ValueError, TypeError):
                        pass

            if not doc_issues:
                formally_correct += 1
            else:
                issues_per_doc[idx] = doc_issues

        n = len(documents)
        rate = formally_correct / n if n > 0 else 0.0
        result.metrics.formal_correctness_rate = round(rate, 4)

        # B-12: Warnung wenn 100% behauptet aber nicht tatsächlich
        if rate < 1.0:
            incorrect_count = n - formally_correct
            result.findings.append(
                WatchdogFinding(
                    category=FindingCategory.FORMAL_CORRECTNESS,
                    level=EscalationLevel.WARNING if rate > 0.5 else EscalationLevel.BLOCKER,
                    document_index=None,
                    field_name=None,
                    message_de=(
                        f"Formale Korrektheit: {formally_correct}/{n} Belege "
                        f"({rate:.1%}) sind formal korrekt. "
                        f"{incorrect_count} Beleg(e) weisen Mängel auf."
                    ),
                    message_en=(
                        f"Formal correctness: {formally_correct}/{n} documents "
                        f"({rate:.1%}) are formally correct. "
                        f"{incorrect_count} document(s) have deficiencies."
                    ),
                    evidence={
                        "correct_count": formally_correct,
                        "total_count": n,
                        "rate": rate,
                        "issues_by_document": {
                            str(k): v for k, v in list(issues_per_doc.items())[:10]
                        },
                    },
                )
            )

    # =========================================================================
    # C-12/C-13: OCR-Confidence-Metriken
    # =========================================================================

    def _calculate_ocr_metrics(
        self, confidences: list[float | None], result: WatchdogResult
    ) -> None:
        """Berechnet OCR-Confidence-Metriken."""
        valid = [c for c in confidences if c is not None]
        if not valid:
            return

        result.metrics.avg_ocr_confidence = round(sum(valid) / len(valid), 4)
        result.metrics.min_ocr_confidence = round(min(valid), 4)

        # C-13: Belege mit Confidence unter 80% markieren
        low_confidence_count = 0
        for idx, conf in enumerate(confidences):
            if conf is not None and conf < 0.80:
                low_confidence_count += 1
                result.findings.append(
                    WatchdogFinding(
                        category=FindingCategory.MANDATORY_FIELD,
                        level=EscalationLevel.INFO,
                        document_index=idx,
                        field_name="ocr_confidence",
                        message_de=(
                            f"Beleg {idx + 1}: OCR-Confidence niedrig "
                            f"({conf:.1%} < 80%). Risikoorientierte Nachprüfung empfohlen."
                        ),
                        message_en=(
                            f"Document {idx + 1}: OCR confidence low "
                            f"({conf:.1%} < 80%). Risk-oriented review recommended."
                        ),
                        evidence={"ocr_confidence": conf},
                    )
                )

        if low_confidence_count > 0:
            result.metrics.escalated_documents += low_confidence_count

    # =========================================================================
    # C-10: Eskalationsstufe bestimmen
    # =========================================================================

    def _determine_escalation(self, result: WatchdogResult) -> None:
        """
        Bestimmt die Eskalationsstufe basierend auf den Befunden.

        Stufe 1 (Info): Auffälligkeit dokumentiert, Analyse läuft weiter.
        Stufe 2 (Warnung): Beleg gelb markiert, manuelle Nachprüfung empfohlen.
        Stufe 3 (Blockade): >20% fehlerhafte Belege, manuelle Freigabe nötig.
        """
        n = result.metrics.total_documents
        if n == 0:
            return

        has_warnings = any(f.level == EscalationLevel.WARNING for f in result.findings)
        has_blockers = any(f.level == EscalationLevel.BLOCKER for f in result.findings)

        # Berechne Fehlerrate (Belege mit mindestens einem Warning/Blocker)
        docs_with_issues: set[int] = set()
        for finding in result.findings:
            if (
                finding.level in (EscalationLevel.WARNING, EscalationLevel.BLOCKER)
                and finding.document_index is not None
            ):
                docs_with_issues.add(finding.document_index)

        error_rate = len(docs_with_issues) / n if n > 0 else 0.0

        if has_blockers or error_rate > self.block_threshold:
            result.escalation_level = EscalationLevel.BLOCKER
            result.report_blocked = True
            result.block_reason = (
                f"{len(docs_with_issues)}/{n} Belege ({error_rate:.1%}) "
                f"weisen Extraktionsfehler auf (Schwelle: {self.block_threshold:.0%}). "
                f"Manuelle Freigabe erforderlich."
            )
            result.metrics.escalated_documents = len(docs_with_issues)
        elif has_warnings:
            result.escalation_level = EscalationLevel.WARNING
            result.metrics.escalated_documents = len(docs_with_issues)
        else:
            result.escalation_level = EscalationLevel.INFO

    # =========================================================================
    # Hilfsmethoden
    # =========================================================================

    @staticmethod
    def _is_empty_or_invalid(value: object) -> bool:
        """Prüft ob ein Wert leer, None, NaN oder ein Platzhalter ist."""
        if value is None:
            return True
        s = str(value).strip().lower()
        if not s:
            return True
        if s in {"nan", "null", "undefined", "none", "n/a", "invalid date", "-"}:
            return True
        try:
            f = float(value)  # type: ignore[arg-type]
            if math.isnan(f):
                return True
        except (ValueError, TypeError):
            pass
        return False

    @staticmethod
    def _to_decimal(value: object) -> Decimal | None:
        """Konvertiert einen Wert sicher in Decimal."""
        if value is None:
            return None
        try:
            s = str(value).replace(",", ".").strip()
            if s.lower() in {"nan", "null", "undefined", "none", "n/a", ""}:
                return None
            d = Decimal(s)
            if d.is_nan() or d.is_infinite():
                return None
            return d
        except (InvalidOperation, ValueError, TypeError):
            return None

    @staticmethod
    def _to_float(value: object) -> float | None:
        """Konvertiert einen Wert sicher in float."""
        if value is None:
            return None
        try:
            s = str(value).replace(",", ".").strip().rstrip("%")
            f = float(s)
            if math.isnan(f) or math.isinf(f):
                return None
            return f
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _try_parse_date(date_str: str) -> date | None:
        """Versucht ein Datum aus verschiedenen Formaten zu parsen."""
        formats = [
            "%d.%m.%Y",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%d-%m-%Y",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _normalize_supplier_name(name: str | None) -> str:
        """Normalisiert Lieferantennamen für Vergleiche."""
        if not name:
            return ""
        s = str(name).strip().lower()
        # Rechtsformen normalisieren
        for suffix in [" gmbh", " ag", " ohg", " kg", " e.k.", " gbr", " mbh"]:
            s = s.replace(suffix, "")
        return s.strip()


# =============================================================================
# Convenience-Funktion
# =============================================================================


def validate_extraction_quality(
    documents: list[dict[str, Any]],
    total_volume: float | None = None,
    ocr_confidences: list[float | None] | None = None,
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
