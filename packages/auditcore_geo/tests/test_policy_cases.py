"""Katalogfälle des Frameworks (T-11, T-14); T-37/T-38 siehe tools/policy_proof.py."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import auditcore_geo
from auditcore_geo import KUGEL_MITTLERER_RADIUS, Punkt, umkreis


def test_t14_library_writes_no_logs() -> None:
    package = Path(auditcore_geo.__file__).parent
    for path in package.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] + [getattr(node, "module", "") or ""]
                assert "logging" not in {n.split(".")[0] for n in names}, path.name


def test_t11_locations_are_processed_in_memory_only() -> None:
    """Standorte (ggf. Anschriften natürlicher Personen) werden nur im Speicher verarbeitet."""
    vorher = {n: getattr(auditcore_geo, n) for n in auditcore_geo.__all__}
    treffer = umkreis(Punkt(50.0, 8.0), [Punkt(50.01, 8.0)], 5_000.0, KUGEL_MITTLERER_RADIUS)
    assert [t.index for t in treffer] == [0]
    assert {n: getattr(auditcore_geo, n) for n in auditcore_geo.__all__} == vorher


def test_t11_geocoder_records_contain_no_contact_or_agent() -> None:
    """Kontaktadresse und Kennung werden gesendet, aber nie im Datensatz gespeichert."""
    from auditcore_harvest import HarvestEngine, Response
    from auditcore_harvest.memory import (
        ClockSleeper,
        FixedClock,
        ListSink,
        MemoryStateStore,
        StaticCredentials,
    )

    from auditcore_geo.nominatim import NominatimAdapter, empfohlene_laufparameter

    class _T:
        def request(self, method: str, url: str, **kwargs: object) -> Response:
            return Response(200, b"[]", {}, url)

    konfig = {
        "anfragen": [{"id": "a", "q": "Musterweg 1, Musterstadt"}],
        "user_agent": "policy-test/1.0 kontakt@example.invalid",
        "email": "kontakt@example.invalid",
        "budget": 1,
        "laufart": "einmalig",
    }
    clock = FixedClock()
    rate, request = empfohlene_laufparameter(konfig, "p", heute_bereits_gesendet=0)
    sink = ListSink()
    HarvestEngine(
        _T(), StaticCredentials({}), MemoryStateStore(), clock, ClockSleeper(clock), rate_limit=rate
    ).run(NominatimAdapter(), request, sink, config=konfig)
    text = json.dumps([r.normalized for r in sink.records.values()], ensure_ascii=False)
    assert "example.invalid" not in text and "policy-test" not in text
