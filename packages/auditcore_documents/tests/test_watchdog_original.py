"""
Originaltests aus flowinvoice (tests/test_extraction_quality_watchdog.py,
Blob 3606ddc1350949ace2153c0078f0d62df81f95fd@fb2d185).

Aussagen unverändert, Import auf die Bibliothek umgestellt.

Tests fuer den Extraktionsqualitaets-Watchdog.

Verifiziert die Implementierung der Anforderungen C-01 bis C-13
des Verbesserungskatalogs HA-EFRE-2026-0847.
"""

import json

from auditcore_documents.pipeline.watchdog import (
    EscalationLevel,
    FindingCategory,
    validate_extraction_quality,
)

# =============================================================================
# Testdaten
# =============================================================================


def _make_valid_document(idx: int = 1) -> dict:
    """Erzeugt ein vollstaendiges, gueltiges Beleg-Dict."""
    return {
        "supplier_name": f"Lieferant {idx} GmbH",
        "customer_name": "Empfaenger AG",
        "supplier_vat_id": f"DE{100000000 + idx}",
        "invoice_date": "15.01.2026",
        "invoice_number": f"2026-{idx:04d}",
        "description": f"Dienstleistung {idx}",
        "net_amount": 1000.00 + idx,
        "vat_rate": 19.0,
        "vat_amount": 190.00 + idx * 0.19,
        "gross_amount": 1190.00 + idx * 1.19,
    }


def _make_invalid_date_document(idx: int = 1) -> dict:
    """Beleg mit Invalid Date (C-02 Fehlerfall)."""
    doc = _make_valid_document(idx)
    doc["invoice_date"] = "Invalid Date"
    return doc


def _make_bad_invoice_number_document(idx: int = 1) -> dict:
    """Beleg mit fehlerhafter Rechnungsnummer (C-03 Fehlerfall)."""
    doc = _make_valid_document(idx)
    doc["invoice_number"] = "100% erneuerbar"
    return doc


# =============================================================================
# C-01: Pflichtfeldvalidierung
# =============================================================================


class TestMandatoryFields:
    """Tests fuer C-01: Pflichtfelder nach § 14 UStG."""

    def test_all_fields_present(self):
        """Alle Pflichtfelder vorhanden -> keine Befunde."""
        docs = [_make_valid_document(i) for i in range(5)]
        result = validate_extraction_quality(docs)

        mandatory_findings = [
            f for f in result.findings if f.category == FindingCategory.MANDATORY_FIELD
        ]
        assert len(mandatory_findings) == 0
        assert result.metrics.mandatory_fields_success_rate == 1.0

    def test_missing_supplier_name(self):
        """Fehlender Lieferantenname -> Warning."""
        doc = _make_valid_document()
        doc["supplier_name"] = None
        result = validate_extraction_quality([doc])

        findings = [f for f in result.findings if f.category == FindingCategory.MANDATORY_FIELD]
        assert len(findings) == 1
        # Der Watchdog benennt das Feld nach § 14 UStG, nicht umgangssprachlich.
        assert "Leistenden" in findings[0].evidence.get("missing_fields", [""])[0]

    def test_nan_value_counts_as_missing(self):
        """NaN-Wert zaehlt als fehlendes Pflichtfeld."""
        doc = _make_valid_document()
        doc["net_amount"] = "NaN"
        result = validate_extraction_quality([doc])

        assert result.metrics.mandatory_fields_success_rate < 1.0


# =============================================================================
# C-02: Datumsvalidierung
# =============================================================================


class TestDateValidation:
    """Tests fuer C-02: Datumsformat-Validierung."""

    def test_valid_german_date(self):
        """Deutsches Datumsformat TT.MM.JJJJ -> OK."""
        doc = _make_valid_document()
        doc["invoice_date"] = "15.01.2026"
        result = validate_extraction_quality([doc])

        date_findings = [
            f for f in result.findings if f.category == FindingCategory.DATE_VALIDATION
        ]
        assert len(date_findings) == 0

    def test_valid_iso_date(self):
        """ISO-Datumsformat JJJJ-MM-TT -> OK."""
        doc = _make_valid_document()
        doc["invoice_date"] = "2026-01-15"
        result = validate_extraction_quality([doc])

        date_findings = [
            f for f in result.findings if f.category == FindingCategory.DATE_VALIDATION
        ]
        assert len(date_findings) == 0

    def test_invalid_date_detected(self):
        """'Invalid Date' -> Warning."""
        doc = _make_invalid_date_document()
        result = validate_extraction_quality([doc])

        date_findings = [
            f for f in result.findings if f.category == FindingCategory.DATE_VALIDATION
        ]
        assert len(date_findings) == 1
        assert date_findings[0].level == EscalationLevel.WARNING

    def test_nan_date_detected(self):
        """'NaN' als Datum -> Warning."""
        doc = _make_valid_document()
        doc["invoice_date"] = "NaN"
        result = validate_extraction_quality([doc])

        date_findings = [
            f for f in result.findings if f.category == FindingCategory.DATE_VALIDATION
        ]
        assert len(date_findings) == 1


# =============================================================================
# C-03: Rechnungsnummern-Plausibilitaet
# =============================================================================


class TestInvoiceNumbers:
    """Tests fuer C-03: Rechnungsnummern-Validierung."""

    def test_valid_invoice_number(self):
        """Normale Rechnungsnummer -> OK."""
        doc = _make_valid_document()
        doc["invoice_number"] = "2026-0042"
        result = validate_extraction_quality([doc])

        inv_findings = [f for f in result.findings if f.category == FindingCategory.INVOICE_NUMBER]
        assert len(inv_findings) == 0

    def test_freetext_invoice_number(self):
        """Fliesstext als Rechnungsnummer -> Warning."""
        doc = _make_bad_invoice_number_document()
        result = validate_extraction_quality([doc])

        inv_findings = [f for f in result.findings if f.category == FindingCategory.INVOICE_NUMBER]
        assert len(inv_findings) == 1

    def test_vat_id_as_invoice_number(self):
        """USt-IdNr. als Rechnungsnummer -> Warning."""
        doc = _make_valid_document()
        doc["invoice_number"] = "USt:I: D. D. E606421989"
        result = validate_extraction_quality([doc])

        inv_findings = [f for f in result.findings if f.category == FindingCategory.INVOICE_NUMBER]
        assert len(inv_findings) >= 1


# =============================================================================
# C-04: Querfeldplausibilitaet
# =============================================================================


class TestCrossFieldPlausibility:
    """Tests fuer C-04: Brutto = Netto + USt."""

    def test_consistent_amounts(self):
        """Konsistente Betraege -> keine Befunde."""
        doc = _make_valid_document()
        doc["net_amount"] = 100.0
        doc["vat_amount"] = 19.0
        doc["gross_amount"] = 119.0
        result = validate_extraction_quality([doc])

        cross_findings = [f for f in result.findings if f.category == FindingCategory.CROSS_FIELD]
        assert len(cross_findings) == 0

    def test_sum_mismatch(self):
        """Brutto != Netto + USt -> Warning."""
        doc = _make_valid_document()
        doc["net_amount"] = 100.0
        doc["vat_amount"] = 19.0
        doc["gross_amount"] = 120.50  # Falsch!
        result = validate_extraction_quality([doc])

        cross_findings = [f for f in result.findings if f.category == FindingCategory.CROSS_FIELD]
        assert len(cross_findings) >= 1


# =============================================================================
# C-05: Steuersatz-Validierung
# =============================================================================


class TestVatRates:
    """Tests fuer C-05: Gesetzlich zulaessige Steuersaetze."""

    def test_valid_rates(self):
        """Gueltige Steuersaetze (0%, 7%, 19%) -> OK."""
        for rate in [0.0, 7.0, 19.0]:
            doc = _make_valid_document()
            doc["vat_rate"] = rate
            result = validate_extraction_quality([doc])

            rate_findings = [
                f
                for f in result.findings
                if f.category == FindingCategory.VAT_RATE and f.document_index is not None
            ]
            assert len(rate_findings) == 0, f"Rate {rate} should be valid"

    def test_invalid_rate(self):
        """Ungueltiger Steuersatz -> Warning."""
        doc = _make_valid_document()
        doc["vat_rate"] = 15.0
        result = validate_extraction_quality([doc])

        rate_findings = [
            f
            for f in result.findings
            if f.category == FindingCategory.VAT_RATE and f.document_index is not None
        ]
        assert len(rate_findings) == 1

    def test_uniform_rate_warning(self):
        """Alle gleicher Steuersatz bei > 5 Belegen -> Info."""
        docs = [_make_valid_document(i) for i in range(10)]
        result = validate_extraction_quality(docs)

        rate_findings = [
            f
            for f in result.findings
            if f.category == FindingCategory.VAT_RATE and f.document_index is None
        ]
        assert len(rate_findings) == 1


# =============================================================================
# C-06: Lieferantennamen-Plausibilitaet
# =============================================================================


class TestSupplierNames:
    """Tests fuer C-06: Lieferantennamen-Validierung."""

    def test_lowercase_only_name(self):
        """Komplett kleingeschriebener Name -> Warning."""
        doc = _make_valid_document()
        doc["supplier_name"] = "fahrzeug"
        result = validate_extraction_quality([doc])

        name_findings = [f for f in result.findings if f.category == FindingCategory.SUPPLIER_NAME]
        assert len(name_findings) == 1


# =============================================================================
# C-07: Lieferanten-Konzentrationsrisiko
# =============================================================================


class TestSupplierConcentration:
    """Tests fuer C-07: Konzentrationsrisiko."""

    def test_concentration_detected(self):
        """Ein Lieferant > 30% -> Warning."""
        docs = []
        for i in range(10):
            doc = _make_valid_document(i)
            if i < 7:
                doc["supplier_name"] = "FlowAudit Testprojekt GmbH"
            else:
                doc["supplier_name"] = f"Lieferant {i} AG"
            docs.append(doc)

        result = validate_extraction_quality(docs)

        conc_findings = [f for f in result.findings if f.category == FindingCategory.CONCENTRATION]
        assert len(conc_findings) >= 1


# =============================================================================
# C-08: Summenabgleich
# =============================================================================


class TestSumReconciliation:
    """Tests fuer C-08: Summenabgleich."""

    def test_matching_sum(self):
        """Summe stimmt -> keine Befunde."""
        docs = [
            {**_make_valid_document(1), "gross_amount": 500.0},
            {**_make_valid_document(2), "gross_amount": 500.0},
        ]
        result = validate_extraction_quality(docs, total_volume=1000.0)

        sum_findings = [
            f for f in result.findings if f.category == FindingCategory.SUM_RECONCILIATION
        ]
        assert len(sum_findings) == 0

    def test_mismatching_sum(self):
        """Summe stimmt nicht -> Warning."""
        docs = [
            {**_make_valid_document(1), "gross_amount": 500.0},
            {**_make_valid_document(2), "gross_amount": 500.0},
        ]
        result = validate_extraction_quality(docs, total_volume=1200.0)

        sum_findings = [
            f for f in result.findings if f.category == FindingCategory.SUM_RECONCILIATION
        ]
        assert len(sum_findings) == 1


# =============================================================================
# C-09: Duplikatpruefung
# =============================================================================


class TestDuplicates:
    """Tests fuer C-09: Duplikaterkennung."""

    def test_duplicate_detected(self):
        """Gleicher Lieferant + gleiche Re.-Nr. -> Warning."""
        doc1 = _make_valid_document(1)
        doc2 = _make_valid_document(2)
        doc2["supplier_name"] = doc1["supplier_name"]
        doc2["invoice_number"] = doc1["invoice_number"]

        result = validate_extraction_quality([doc1, doc2])

        dup_findings = [f for f in result.findings if f.category == FindingCategory.DUPLICATE]
        assert len(dup_findings) == 1

    def test_same_number_different_supplier_ok(self):
        """Gleiche Re.-Nr. bei verschiedenen Lieferanten -> OK."""
        doc1 = _make_valid_document(1)
        doc2 = _make_valid_document(2)
        doc1["invoice_number"] = "2026-0002"
        doc2["invoice_number"] = "2026-0002"
        # Different suppliers

        result = validate_extraction_quality([doc1, doc2])

        dup_findings = [f for f in result.findings if f.category == FindingCategory.DUPLICATE]
        assert len(dup_findings) == 0


# =============================================================================
# C-10: Eskalationsmodell
# =============================================================================


class TestEscalation:
    """Tests fuer C-10: Dreistufiges Eskalationsmodell."""

    def test_all_valid_no_escalation(self):
        """Alle Belege OK -> Info-Level, kein Block."""
        docs = [_make_valid_document(i) for i in range(5)]
        result = validate_extraction_quality(docs)

        assert result.escalation_level == EscalationLevel.INFO
        assert result.report_blocked is False

    def test_warnings_escalate_to_warning(self):
        """Belege mit Warnungen -> Warning-Level."""
        docs = [_make_invalid_date_document(i) for i in range(2)]
        docs.extend([_make_valid_document(i) for i in range(8)])
        result = validate_extraction_quality(docs)

        assert result.escalation_level == EscalationLevel.WARNING
        assert result.report_blocked is False

    def test_high_error_rate_blocks_report(self):
        """> 20% fehlerhafte Belege -> Blockade."""
        # 5 von 10 Belegen fehlerhaft (50% > 20%)
        docs = [_make_invalid_date_document(i) for i in range(5)]
        docs.extend([_make_valid_document(i) for i in range(5)])
        result = validate_extraction_quality(docs)

        assert result.escalation_level == EscalationLevel.BLOCKER
        assert result.report_blocked is True
        assert result.block_reason is not None


# =============================================================================
# C-11: JSON-Export
# =============================================================================


class TestJsonExport:
    """Tests fuer C-11: Maschinenlesbarer JSON-Export."""

    def test_json_export(self):
        """Ergebnis ist als JSON exportierbar."""
        docs = [_make_valid_document(1), _make_invalid_date_document(2)]
        result = validate_extraction_quality(docs)

        json_str = result.to_json()
        data = json.loads(json_str)

        assert "findings" in data
        assert "metrics" in data
        assert "escalation_level" in data
        assert "report_blocked" in data
        assert "timestamp" in data


# =============================================================================
# B-12: Formale Korrektheit
# =============================================================================


class TestFormalCorrectness:
    """Tests fuer B-12: Tatsaechliche formale Korrektheit."""

    def test_all_correct(self):
        """Alle Belege formal korrekt -> 100%."""
        docs = [_make_valid_document(i) for i in range(5)]
        result = validate_extraction_quality(docs)

        assert result.metrics.formal_correctness_rate == 1.0

    def test_invalid_date_reduces_correctness(self):
        """'Invalid Date' reduziert formale Korrektheit."""
        docs = [_make_valid_document(1), _make_invalid_date_document(2)]
        result = validate_extraction_quality(docs)

        assert result.metrics.formal_correctness_rate < 1.0

    def test_missing_field_reduces_correctness(self):
        """Fehlendes Pflichtfeld reduziert formale Korrektheit."""
        doc = _make_valid_document(1)
        doc["supplier_name"] = None
        result = validate_extraction_quality([doc])

        assert result.metrics.formal_correctness_rate < 1.0


# =============================================================================
# A-07: NaN-Pruefung
# =============================================================================


class TestNanValues:
    """Tests fuer A-07: NaN/Null/undefined-Schutz."""

    def test_nan_detected(self):
        """NaN in numerischem Feld -> Warning."""
        doc = _make_valid_document()
        doc["net_amount"] = float("nan")
        result = validate_extraction_quality([doc])

        nan_findings = [f for f in result.findings if f.category == FindingCategory.NAN_VALUE]
        assert len(nan_findings) >= 1

    def test_nan_string_detected(self):
        """'NaN' als String -> Warning."""
        doc = _make_valid_document()
        doc["vat_amount"] = "NaN"
        result = validate_extraction_quality([doc])

        nan_findings = [f for f in result.findings if f.category == FindingCategory.NAN_VALUE]
        assert len(nan_findings) >= 1
