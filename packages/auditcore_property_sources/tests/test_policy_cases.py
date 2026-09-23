"""Framework catalogue cases T-11, T-14 and T-30 for this library."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from support import FIXTURES, observed, page, replay, run

import auditcore_property_sources
from auditcore_property_sources import bienici, inberlinwohnen
from auditcore_property_sources.adapters import InBerlinWohnenAdapter

PHONE = re.compile(r"(?:\+\d{2}\s?|\b0)\d{2,5}[\s/-]\d{4,}\b|\btel(?:efon)?\.?:", re.I)
MAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def test_t11_fixtures_hold_no_personal_contact_data_and_private_names_are_minimised() -> None:
    for path in FIXTURES.rglob("*"):
        if path.is_file() and path.parent.name != "robots":
            text = path.read_text(encoding="utf-8")
            if path.name == "legacy_observed.json":
                data = json.loads(text)
                text = json.dumps(
                    [c for c in data["cases"] if c["function"] != "decode_portal_response"]
                )
            assert not MAIL.search(text), path
            assert not PHONE.search(text), path
    ad = {"id": "1", "accountType": "individual", "accountDisplayName": "M. Exemple"}
    assert bienici.normalise(ad, advertiser_names="minimal")["gesellschaft"] == "Privatangebot"
    assert bienici.normalise(ad)["gesellschaft"] == "M. Exemple"  # PS-C02 DECIDED: legacy
    assert observed()["inputs"].startswith("synthetic")


def test_t14_library_does_not_log_and_results_carry_no_headers() -> None:
    package = Path(auditcore_property_sources.__file__).parent
    for path in package.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] + [getattr(node, "module", "") or ""]
                assert "logging" not in {n.split(".")[0] for n in names}, path.name
    web = {inberlinwohnen.page_url(1): page("inberlinwohnen/leer.html")}
    result, _ = run(InBerlinWohnenAdapter(), replay(web, robots=None), {})
    text = json.dumps(result.to_dict())
    assert "User-Agent" not in text and "Referer" not in text


def test_t30_records_carry_profile_and_adapter_version_and_errors_are_visible() -> None:
    web = {
        inberlinwohnen.page_url(1): page("inberlinwohnen/seite-1.html"),
        inberlinwohnen.page_url(2): page("inberlinwohnen/leer.html"),
    }
    result, sink = run(InBerlinWohnenAdapter(), replay(web, robots=None), {})
    assert result.status.value == "partial" and "Snapshot" in result.issues[0].message
    for record in sink.records.values():
        assert record.provenance.profile_version == "2026.09.1"
        assert record.provenance.adapter_version == "1.1.0"
        assert record.provenance.raw_sha256
