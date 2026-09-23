"""Wiedergabe des flowinvoice-Watchdogs gegen die aufgezeichneten Originalergebnisse.

Entscheidung D8 (2026-09-23): Die Bibliothek schreibt deutsche Meldungen mit
echten Umlauten. Nach Rückumschrift (ä→ae, ö→oe, ü→ue, ß→ss) muss das
Ergebnis dem unveränderten Original exakt entsprechen.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from auditcore_documents.pipeline.watchdog import ExtractionQualityWatchdog

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from capture_watchdog import scenarios, watchdog_kwargs  # noqa: E402

OBSERVED = json.loads(
    (Path(__file__).parent / "fixtures" / "watchdog_observed.json").read_text(encoding="utf-8")
)
TRANSLIT = str.maketrans(
    {"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss"}
)
CASES = {case["name"]: case for case in scenarios()}


def run(case: dict[str, Any]) -> dict[str, Any]:
    watchdog = ExtractionQualityWatchdog(
        **watchdog_kwargs(case.get("watchdog", {})),
        clock=lambda: datetime(2026, 9, 23, tzinfo=UTC),
    )
    result = watchdog.validate(
        case["documents"],
        total_volume=case.get("total_volume"),
        ocr_confidences=case.get("ocr_confidences"),
    )
    observed: dict[str, Any] = json.loads(result.to_json())
    assert observed["timestamp"] == "2026-09-23T00:00:00+00:00"
    observed["timestamp"] = "<masked>"
    return observed


def translit(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False).translate(TRANSLIT))


def test_all_scenarios_recorded() -> None:
    assert sorted(CASES) == sorted(s["name"] for s in OBSERVED["scenarios"])


@pytest.mark.parametrize("recorded", OBSERVED["scenarios"], ids=lambda s: s["name"])
def test_watchdog_matches_original_after_transliteration(recorded: dict[str, Any]) -> None:
    ours = run(CASES[recorded["name"]])
    assert translit(ours) == translit(recorded["observed"])


def test_messages_use_real_umlauts() -> None:
    texts = []
    for case in CASES.values():
        ours = run(case)
        texts += [f["message_de"] for f in ours["findings"]]
        texts.append(ours["block_reason"] or "")
        for finding in ours["findings"]:
            for issues in finding["evidence"].get("issues_by_document", {}).values():
                texts += issues
    joined = "\n".join(texts)
    for word in ("Nachprüfung", "Mängel", "ungültig", "Mögliches", "verdächtiger", "Großbuchstabe"):
        assert word in joined
    for legacy in ("Nachpruefung", "Maengel", "ungueltig", "Moegliches", "verdaechtiger"):
        assert legacy not in joined


def test_input_patterns_unchanged() -> None:
    doc = CASES["rechnungsnummer"]["documents"]
    ours = run({"documents": doc})
    issues = [i for f in ours["findings"] for i in f["evidence"].get("issues", [])]
    assert "verdächtiger Inhalt (enthält 'steuer')" in issues
