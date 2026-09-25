"""Renamed public names stay importable with a deprecation warning."""

from __future__ import annotations

import importlib

import pytest

import auditcore_price_sources
from auditcore_price_sources.destatis import DestatisTableAdapter


@pytest.mark.parametrize("module", ["auditcore_price_sources", "auditcore_price_sources.destatis"])
def test_old_destatis_name_warns_and_is_the_new_class(module: str) -> None:
    with pytest.warns(DeprecationWarning, match="DestatisTableAdapter"):
        old = importlib.import_module(module).DestatisTabellenAdapter
    assert old is DestatisTableAdapter


def test_registry_uses_the_new_class() -> None:
    factory = auditcore_price_sources.FACTORIES["price.destatis_genesis"]
    assert factory is DestatisTableAdapter
