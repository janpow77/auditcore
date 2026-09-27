"""Invarianten I11 bis I16 der Bestandsprüfung und der Regelmeldungen (Hypothesis).

Synthetische Belege erfundener Lieferanten; keine Dateien, kein Netz.
"""

from __future__ import annotations

import csv
import io
import json
import re
from datetime import UTC, datetime

from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_documents.pipeline.stages.rule_messages import (
    RULE_MESSAGES,
    german_message,
    original_message,
    say,
)
from auditcore_documents.pipeline.watchdog import WatchdogResult
from auditcore_documents.pipeline.watchdog.inventory_checks import (
    MAX_NUMBER_GAP,
    check_invoice_number_gaps,
)
from auditcore_documents.web import BatchCheckService
from auditcore_documents.web.batch_rules import RULES_BY_CODE

EXAMPLES = settings(max_examples=60, deadline=None)
SERVICE = BatchCheckService(clock=lambda: datetime(2026, 9, 27, tzinfo=UTC))
SUPPLIERS = st.sampled_from(["Muster Bau GmbH", "Muster Bau", "Beispiel AG", "demo", "", "12"])
NUMBERS = st.one_of(
    st.integers(0, 40).map(lambda n: f"RE-{n:03d}"),
    st.sampled_from(["", "Steuer 1 2 3 4", "A-1", "=X"]),
)
AMOUNTS = st.one_of(
    st.none(),
    st.integers(0, 5000),
    st.sampled_from(["1.234,56", "NaN", "abc", "0,00"]),
)
DATES = st.sampled_from(["15.01.2026", "2026-01-15", "Invalid Date", "", "32.13.2026"])
DOCUMENT = st.fixed_dictionaries(
    {
        "supplier_name": SUPPLIERS,
        "invoice_number": NUMBERS,
        "invoice_date": DATES,
        "supplier_vat_id": st.sampled_from(["DE100000001", "DE100000009", "012/345/67890", ""]),
        "customer_name": st.sampled_from(["Beispielverein e. V.", ""]),
        "description": st.sampled_from(["Leistung", ""]),
        "net_amount": AMOUNTS,
        "vat_rate": st.sampled_from([0, 7, 19, 16, None]),
        "vat_amount": AMOUNTS,
        "gross_amount": AMOUNTS,
        "ocr_confidence": st.one_of(st.none(), st.floats(0, 1)),
    }
)  # fmt: skip
INVENTORY = st.lists(DOCUMENT, min_size=1, max_size=12)
SAFE_VALUE = st.text(alphabet="abcXYZ0123456789.,%-", min_size=0, max_size=8)


@EXAMPLES
@given(st.sampled_from(sorted(RULE_MESSAGES)), st.data())
def test_i11_rule_messages_convert_both_ways(code: str, data: st.DataObject) -> None:
    """Invariante I11: Regelmeldungen deutsch ↔ Originalwortlaut."""
    entry = RULE_MESSAGES[code]
    names = re.findall(r"\{([a-z_]+)\}", entry.original)
    values = {name: data.draw(SAFE_VALUE) for name in names}
    assert original_message(say(code, **values)) == entry.original.format(**values)
    assert german_message(entry.original.format(**values)) == say(code, **values)


@EXAMPLES
@given(INVENTORY, st.booleans())
def test_i12_answer_accounts_for_every_finding(
    documents: list[dict[str, object]], extra: bool
) -> None:
    """Invariante I12: jeder Befund genau einmal verbucht."""
    answer = SERVICE.check({"documents": documents, "options": {"supplementary": extra}})
    findings = answer["findings"]
    n = len(documents)
    assert answer["summary"]["documents"] == n == len(answer["documents"])
    assert answer["summary"]["findings"] == len(findings)
    assert sum(rule["findings"] for rule in answer["rules"]) == len(findings)
    touched = {i for f in findings for i in f["documents"]}
    assert all(0 <= i < n for i in touched)
    assert answer["summary"]["documents_with_findings"] == len(touched)
    assert all(f["rule"] in RULES_BY_CODE for f in findings)
    assert [f["id"] for f in findings] == [f"B-{k:04d}" for k in range(1, len(findings) + 1)]
    for rule in answer["rules"]:
        assert (rule["status"] == "findings") == (rule["findings"] > 0)


@EXAMPLES
@given(INVENTORY)
def test_i13_export_matches_the_run(documents: list[dict[str, object]]) -> None:
    """Invariante I13: Export entspricht dem Lauf."""
    answer = SERVICE.check({"documents": documents})
    as_json = SERVICE.export({"documents": documents, "format": "json"})
    assert json.loads(as_json.content) == answer
    text = SERVICE.export({"documents": documents, "format": "csv"}).content.decode("utf-8")
    rows = list(csv.reader(io.StringIO(text.lstrip("\ufeff")), delimiter=";"))
    assert len(rows) - 1 == sum(max(1, len(f["documents"])) for f in answer["findings"])


@EXAMPLES
@given(st.sets(st.integers(1, 200), min_size=1, max_size=15))
def test_i14_gaps_lie_between_present_numbers(counters: set[int]) -> None:
    """Invariante I14: Lücken liegen zwischen vorhandenen Nummern."""
    documents = [
        {"supplier_name": "Muster Bau GmbH", "invoice_number": f"RE-{c:03d}"} for c in counters
    ]
    result = WatchdogResult()
    check_invoice_number_gaps(documents, result)
    present = sorted(counters)
    expected = {
        n for low, high in zip(present, present[1:], strict=False)
        if high - low <= MAX_NUMBER_GAP for n in range(low + 1, high)
    }  # fmt: skip
    reported = {
        n for f in result.findings for low, high in f.evidence["gaps"] for n in range(low, high + 1)
    }  # fmt: skip
    assert reported == expected
    assert not reported & counters


@EXAMPLES
@given(INVENTORY)
def test_i15_supplementary_checks_do_not_change_escalation(
    documents: list[dict[str, object]],
) -> None:
    """Invariante I15: Ergänzungen ändern die Eskalation nicht."""
    with_extra = SERVICE.check({"documents": documents, "options": {"supplementary": True}})
    without = SERVICE.check({"documents": documents, "options": {"supplementary": False}})
    assert with_extra["summary"]["escalation_level"] == without["summary"]["escalation_level"]
    assert with_extra["summary"]["report_blocked"] == without["summary"]["report_blocked"]
    assert with_extra["metrics"] == without["metrics"]
    catalogue = [f for f in with_extra["findings"] if not f["rule"].startswith("ERG-")]
    strip = [{k: v for k, v in f.items() if k != "id"} for f in catalogue]
    assert strip == [{k: v for k, v in f.items() if k != "id"} for f in without["findings"]]


EXTRACTION_NAMES = {"invoice_date": "date", "gross_amount": "total", "supplier_vat_id": "vat_id"}


def as_extraction_run(document: dict[str, object], row: int) -> dict[str, object]:
    fields = [
        {"name": EXTRACTION_NAMES.get(key, key), "value": value}
        for key, value in document.items()
        if key != "ocr_confidence"
    ]
    return {
        "contract": "documents_extraction/1",
        "document": {"filename": f"Beleg {row}"},
        "ocr": {"avg_confidence": document["ocr_confidence"]},
        "fields": fields,
    }


@EXAMPLES
@given(INVENTORY)
def test_i16_extraction_runs_equal_flat_records(documents: list[dict[str, object]]) -> None:
    """Invariante I16: Lauf der Belegerkennung = flacher Datensatz."""
    runs = [as_extraction_run(d, row) for row, d in enumerate(documents, start=1)]
    flat = SERVICE.check({"documents": documents})
    converted = SERVICE.check({"documents": runs})
    assert converted["findings"] == flat["findings"]
    assert converted["rules"] == flat["rules"]
    assert converted["documents"] == flat["documents"]
