"""Framework catalogue cases (verwaltung-app-framework docs/pruefkatalog.md) for this library.

T-09 export scope, T-14 protocol content, T-30 import mapping. T-37 (SBOM) and
T-38 (architecture) are bound by ``tools/policy_proof.py``.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from auditcore_harvest import HarvestEngine, HarvestRequest
from auditcore_harvest.memory import (
    ClockSleeper,
    FixedClock,
    ListSink,
    MemoryStateStore,
    StaticCredentials,
)
from page_replay import PageReplay

import auditcore_procurement
from auditcore_procurement import records, sources, ted

REPLAY = Path(__file__).parent / "fixtures" / "replay"
AWARD = {"publication-number": "1-2024", "winner-name": "A GmbH", "result-value-notice": "10"}


def test_t09_json_export_keeps_count_fields_and_contract() -> None:
    selected = [
        ted.normalize_notice({**AWARD, "publication-number": f"{i}-2024"}) for i in range(4)
    ]
    exported = json.loads(ted.dump_records([r for r in selected if r]))
    assert len(exported) == 4 and exported[0] == selected[0]
    back, columns, validation = ted.parse_ted_file(ted.dump_records(exported), "export.json")
    assert (
        back == exported and columns == list(records.NOTICE_FIELDS) and validation["errors"] == []
    )


def test_t14_library_does_not_log_and_results_contain_no_request_secrets() -> None:
    package = Path(auditcore_procurement.__file__).parent
    for path in package.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] + [getattr(node, "module", "") or ""]
                assert "logging" not in {n.split(".")[0] for n in names}, path.name
    clock = FixedClock()
    result = HarvestEngine(
        transport=PageReplay.from_file(REPLAY / "ted_awards.json"),
        credentials=StaticCredentials({}),
        state=MemoryStateStore(),
        clock=clock,
        sleeper=ClockSleeper(clock),
    ).run(
        sources.TedAwardsAdapter(),
        HarvestRequest(sources.TED_SOURCE_ID, run_id="t14"),
        ListSink(),
        config={"api_url": "https://api.ted.europa.eu/v3/notices/search", "page_size": 2},
    )
    text = json.dumps(result.to_dict())
    assert "Authorization" not in text and "Content-Type" not in text


def test_t30_field_mapping_variants_errors_and_version_binding() -> None:
    legacy_names = {"ND": "9-2019", "WIN_NAME": "Firma", "PD": "20190301", "CPV": "45000000"}
    assert ted.normalize_notice(legacy_names) == {
        "notice_id": "9-2019",
        "document_number": "9-2019",
        "contractor_name": "Firma",
        "cpv_codes": "45000000",
        "publication_date": "2019-03-01",
    }
    _, _, validation = ted.parse_ted_file(b'[{"publication-number": "x"}]', "fehlt.json")
    assert validation["warnings"] and validation["errors"]
    _, _, broken = ted.parse_ted_file(b"{kaputt", "kaputt.json")
    assert broken["errors"]
    assert [i.code for i in ted.inspect_notice({**AWARD, "publication-date": "gestern"})] == [
        "unparsed_date"
    ]
    sink = ListSink()
    clock = FixedClock()
    HarvestEngine(
        transport=PageReplay.from_file(REPLAY / "ted_awards.json"),
        credentials=StaticCredentials({}),
        state=MemoryStateStore(),
        clock=clock,
        sleeper=ClockSleeper(clock),
    ).run(
        sources.TedAwardsAdapter(),
        HarvestRequest(sources.TED_SOURCE_ID, run_id="t30"),
        sink,
        config={"api_url": "https://api.ted.europa.eu/v3/notices/search", "page_size": 2},
    )
    provenance = next(iter(sink.records.values())).provenance
    assert (provenance.profile_version, provenance.adapter_version) == ("2026.09.1", "1.0.0")
