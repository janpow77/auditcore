"""require_module against the lazy-import blocks of the packages (differential)."""

from __future__ import annotations

import sys
import types

import legacy_reference as legacy
import pytest
from samples import assert_same_outcome

from auditcore_common.optional import require_module

DP = "Excel-Ausgabe benötigt openpyxl: pip install 'auditcore_dataprotection[excel]'"
FUNDING = "XLSX-Dateien benötigen das Extra auditcore_funding_sources[xlsx] (openpyxl)."
FUZZY = "Für unscharfe Vergleiche ist 'auditcore_entity_matching[fuzzy]' zu installieren."


def _fuzzy_new() -> tuple[types.ModuleType, types.ModuleType]:
    return (
        require_module("rapidfuzz.fuzz", legacy.DependencyError, FUZZY),
        require_module("rapidfuzz.process", legacy.DependencyError, FUZZY),
    )


def _cases() -> list[tuple[object, object]]:
    return [
        (
            legacy.dataprotection_openpyxl,
            lambda: require_module("openpyxl", legacy.ExportDependencyError, DP),
        ),
        (
            legacy.funding_openpyxl,
            lambda: require_module("openpyxl", legacy.OptionalDependencyError, FUNDING),
        ),
        (legacy.entity_rapidfuzz, _fuzzy_new),
    ]


def test_missing_module_raises_the_same_error(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("openpyxl", "rapidfuzz", "rapidfuzz.fuzz", "rapidfuzz.process"):
        monkeypatch.setitem(sys.modules, name, None)
    for old, new in _cases():
        assert_same_outcome(old, new)  # type: ignore[arg-type]


def test_present_module_is_returned(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = types.ModuleType("openpyxl")
    rapid = types.ModuleType("rapidfuzz")
    fuzz, process = types.ModuleType("rapidfuzz.fuzz"), types.ModuleType("rapidfuzz.process")
    rapid.fuzz, rapid.process = fuzz, process  # type: ignore[attr-defined]
    rapid.__path__ = []  # type: ignore[attr-defined]
    for name, module in (
        ("openpyxl", fake),
        ("rapidfuzz", rapid),
        ("rapidfuzz.fuzz", fuzz),
        ("rapidfuzz.process", process),
    ):
        monkeypatch.setitem(sys.modules, name, module)
    for old, new in _cases():
        assert_same_outcome(old, new)  # type: ignore[arg-type]
