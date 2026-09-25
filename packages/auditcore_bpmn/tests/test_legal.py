"""Extra ``legal``: Normauflösung mit auditcore_legal_sources; ohne Extra bleibt alles andere nutzbar."""

from __future__ import annotations

import subprocess
import sys

import pytest

from auditcore_bpmn.citations import enrich
from auditcore_bpmn.extensions import LegalBasis
from auditcore_bpmn.profiles import load_profile


def test_resolver_with_catalogue() -> None:
    pytest.importorskip("auditcore_legal_sources")
    from auditcore_bpmn.legal import LegalSourcesNormResolver

    resolver = LegalSourcesNormResolver(period_profile=load_profile())
    resolved = resolver.resolve("VO (EU) 2021/1060")
    assert resolved is not None and resolved.catalogued and resolved.short_title == "Dachverordnung 2021-2027"
    assert resolved.programming_period == "2021-2027" and resolved.source.startswith("auditcore_legal_sources:")
    other = resolver.resolve("Richtlinie 2014/24/EU")
    assert other is not None and not other.catalogued and other.celex == "32014L0024"
    assert resolver.resolve("BHO") is None
    assert (
        resolver.article_title("Verordnung (EU) 2021/1060", "74") == "Programmverwaltung durch die Verwaltungsbehörde"
    )
    assert (
        resolver.article_title("Verordnung (EU) 2021/1060", "74", "en")
        == "Programme management by the managing authority"
    )
    assert resolver.article_title("BHO", "7") is None
    enriched = enrich(LegalBasis(act="VO (EU) 2021/1060", article="74"), resolver)
    assert enriched.short_title == "Dachverordnung 2021-2027" and enriched.celex == "32021R1060"
    assert LegalSourcesNormResolver().article_title("VO (EU) 2021/1060", "74") is None


def test_without_extra_import_fails_cleanly_and_core_works() -> None:
    code = (
        "import sys; sys.modules['auditcore_legal_sources'] = None\n"
        "import auditcore_bpmn\n"
        "from auditcore_bpmn.errors import OptionalDependencyError\n"
        "assert auditcore_bpmn.validate('<bpmn:definitions xmlns:bpmn=\"http://www.omg.org/spec/BPMN/20100524/MODEL\"/>')\n"
        "try:\n    import auditcore_bpmn.legal\nexcept OptionalDependencyError as e:\n    print('ok', 'legal' in str(e))\n"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "ok True"
