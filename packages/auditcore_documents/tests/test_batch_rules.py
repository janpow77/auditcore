"""Ergänzungsprüfungen ERG-01/ERG-02 und deutsche Regelmeldungen der Pipeline (D9)."""

from __future__ import annotations

import re

import pytest

from auditcore_documents.pipeline.stages.rule_messages import (
    RULE_MESSAGES,
    german_message,
    original_message,
    say,
)
from auditcore_documents.pipeline.watchdog import WatchdogResult
from auditcore_documents.pipeline.watchdog.inventory_checks import (
    LISTED_GAPS,
    check_invoice_number_gaps,
    check_vat_id_consistency,
    normalize_vat_id,
)

ASCII_UMLAUT = re.compile(r"(?i)\b\w*(ae|oe|ue)\w*\b")
#: Wörter mit „ae/oe/ue“, die keine Umschrift eines Umlauts sind.
NOT_UMLAUTS = {"steuernummer", "betrugsprüfung", "neue", "prüfung"}


def run(check: object, documents: list[dict[str, object]]) -> WatchdogResult:
    result = WatchdogResult()
    check(documents, result)  # type: ignore[operator]
    return result


def doc(supplier: str, number: str, vat_id: str | None = None) -> dict[str, object]:
    return {"supplier_name": supplier, "invoice_number": number, "supplier_vat_id": vat_id}


def test_gaps_per_supplier_and_series_keep_width() -> None:
    documents = [
        doc("Muster Bau GmbH", "RE-0007"),
        doc("Muster Bau", "RE-0010"),
        doc("Muster Bau GmbH", "RE-0011"),
        doc("Muster Bau GmbH", "AB-3"),
        doc("Muster Bau GmbH", "AB-500"),
        doc("Beispiel AG", "RE-0008"),
    ]
    findings = run(check_invoice_number_gaps, documents).findings
    assert len(findings) == 1
    finding = findings[0]
    assert finding.level == "info" and finding.category == "invoice_number_gap"
    assert "RE-0008 bis RE-0009" in finding.message_de
    assert finding.evidence["missing_count"] == 2
    assert finding.evidence["document_indices"] == [0, 1, 2]


def test_single_missing_number_and_listing_limit() -> None:
    documents = [doc("Muster Bau GmbH", f"N{n}") for n in range(1, 2 * LISTED_GAPS + 4, 2)]
    finding = run(check_invoice_number_gaps, documents).findings[0]
    assert finding.message_de.count(";") == LISTED_GAPS - 1
    assert "N2;" in finding.message_de and "weitere" in finding.message_de
    assert not run(check_invoice_number_gaps, [doc("Muster Bau GmbH", "ohne")]).findings


def test_vat_id_consistency_levels() -> None:
    documents = [
        doc("Muster Bau GmbH", "1", "DE 100 000 001"),
        doc("Muster Bau", "2", "DE100000009"),
        doc("Demo Druck KG", "3", "012/345/67890"),
        doc("Demo Druck KG", "4", "DE400000004"),
        doc("Andere Druck GmbH", "5", "de400000004"),
        doc("Ohne Kennung GmbH", "6", "n/a"),
    ]
    findings = run(check_vat_id_consistency, documents).findings
    levels = {(f.evidence.get("supplier") or f.evidence.get("vat_id")): f.level for f in findings}
    assert levels == {"muster bau": "warning", "demo druck": "info", "DE400000004": "info"}
    assert normalize_vat_id("n/a") == ""


@pytest.mark.parametrize("code", sorted(RULE_MESSAGES))
def test_rule_messages_round_trip(code: str) -> None:
    entry = RULE_MESSAGES[code]
    values = {name: f"<{name}>" for name in re.findall(r"\{([a-z_]+)\}", entry.original)}
    german = say(code, **values)
    assert german == entry.german.format(**values)
    assert original_message(german) == entry.original.format(**values)
    assert german_message(entry.original.format(**values)) == german


def test_rule_messages_use_real_umlauts() -> None:
    for entry in RULE_MESSAGES.values():
        words = {w.lower() for w in re.findall(r"\w+", entry.german)}
        suspicious = {w for w in words if ASCII_UMLAUT.fullmatch(w)} - NOT_UMLAUTS
        assert not suspicious, (entry.code, suspicious)
    assert original_message("Donut-Werte unplausibel: total") == "Donut-Werte unplausibel: total"
